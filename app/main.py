import os
import yaml
from typing import Dict, Any, List, Optional, Literal
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError, create_model, Field
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi

app = FastAPI(
    title="MongoDB FastAPI Backend",
    description="...",
    version="1.0.0",
    root_path="/mongodb",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Leggi la URI da ambiente oppure usa quella di default (non è consigliabile hardcodare le credenziali in produzione)
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://info:mwL6B0q0E1CNSfpz@cluster0.bmfbkbc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)

mongo_client: AsyncIOMotorClient = AsyncIOMotorClient(MONGODB_URI, server_api=ServerApi("1"))  # client globale
db_cache: Dict[str, AsyncIOMotorDatabase] = {}  # caching delle istanze di database

# Cache per gli schemi YAML
schemas: Dict[str, Dict[str, Any]] = {}

# --- Funzioni di Utility --- #

def get_db_instance(db_name: str) -> AsyncIOMotorDatabase:
    """
    Ritorna l'istanza del database specificato utilizzando il client globale.
    Utilizza un caching locale per evitare chiamate ripetute.
    """
    global db_cache, mongo_client
    if db_name in db_cache:
        return db_cache[db_name]
    else:
        db_instance = mongo_client[db_name]
        db_cache[db_name] = db_instance
        return db_instance


async def add_database(db_name: str) -> AsyncIOMotorDatabase:
    """
    In MongoDB il database viene creato in maniera lazy; questa funzione ritorna
    comunque l'istanza del database, memorizzandola nel cache.
    """
    return get_db_instance(db_name)


# Mappa per convertire le stringhe dei tipi in tipi Python sicuri
TYPE_MAP = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "dict": dict,
}


def create_pydantic_model(schema_name: str, schema: Dict[str, Any]):
    """
    Crea un modello Pydantic dinamico basato su uno schema YAML.
    """
    fields = {}
    for field_name, field_props in schema.items():
        type_str = field_props.get("type")
        field_type = TYPE_MAP.get(type_str, str)  # se il tipo non è riconosciuto, fallback a str

        # Supporto per enum
        if "enum" in field_props:
            field_type = Literal[tuple(field_props["enum"])]

        field_args = {}
        if 'title' in field_props:
            field_args['title'] = field_props['title']
        if 'min_length' in field_props:
            field_args['min_length'] = field_props['min_length']
        if 'max_length' in field_props:
            field_args['max_length'] = field_props['max_length']
        if 'default' in field_props:
            field_args['default'] = field_props['default']
        if 'ge' in field_props:
            field_args['ge'] = field_props['ge']
        if 'le' in field_props:
            field_args['le'] = field_props['le']

        fields[field_name] = (field_type, Field(**field_args))

    return create_model(schema_name, **fields)


def validate_input(db_name: str, collection_name: str, data: Dict[str, Any]):
    """
    Valida i dati in ingresso basandosi su uno schema YAML presente nella directory 'allowed_schemas'.
    Se non viene trovato nessuno schema, accetta i dati così come sono.
    """
    schema_dir = os.path.join("allowed_schemas", db_name, collection_name)
    if not os.path.exists(schema_dir) or not os.listdir(schema_dir):
        return data

    schema_files = os.listdir(schema_dir)
    for schema_file in schema_files:
        schema_key = f"{db_name}/{collection_name}/{schema_file}"
        if schema_key not in schemas:
            with open(os.path.join(schema_dir, schema_file), "r") as f:
                schemas[schema_key] = yaml.safe_load(f)

        schema = schemas[schema_key]
        try:
            dynamic_model = create_pydantic_model(schema_file, schema)
            validated_data = dynamic_model(**data)
            return validated_data.dict()
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Errore di validazione: {e.errors()}"
            )
    return data


# --- Modelli Pydantic per gli endpoint API ---

class DBCredentials(BaseModel):
    db_name: str
    username: Optional[str] = None
    password: Optional[str] = None
    host: Optional[str] = "mongodb"  # su Atlas l'host è definito nella URI
    port: Optional[int] = 27017


class SearchQuery(BaseModel):
    field: str
    value: Any
    exact_match: Optional[bool] = True


# Flag per la validazione dei dati tramite schema (può essere attivato/disattivato in base alle esigenze)
DATA_VALIDATION = False


# --- Endpoints API ---

@app.post("/create_database/", summary="Crea un nuovo database",
          response_description="Il database è stato creato con successo")
async def create_database(credentials: DBCredentials):
    """
    Crea un nuovo database e lo connette.

    Input:
      - db_name, username, password, host, port
    Output:
      - Messaggio di successo
    """
    try:
        db = await add_database(credentials.db_name)
        return {"message": f"Database '{credentials.db_name}' created and connected successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Errore nella creazione del database: {str(e)}"
        )


@app.get("/list_databases/", summary="Ottieni l'elenco dei database",
         response_description="Elenco dei database esistenti")
async def list_databases():
    try:
        db_list = await mongo_client.list_database_names()
        return {"databases": db_list}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Errore nel recupero dei database: {str(e)}"
        )


@app.delete("/delete_database/{db_name}/", summary="Elimina un database esistente",
            response_description="Il database è stato eliminato con successo")
async def delete_database(db_name: str):
    try:
        await mongo_client.drop_database(db_name)
        db_cache.pop(db_name, None)
        return {"message": f"Database '{db_name}' deleted successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Errore nell'eliminazione del database: {str(e)}"
        )


@app.post("/{db_name}/create_collection/", summary="Crea una nuova collezione",
          response_description="La collezione è stata creata con successo")
async def create_collection(db_name: str, collection_name: str):
    try:
        db = get_db_instance(db_name)
    except Exception:
        db = await add_database(db_name)
    try:
        await db.create_collection(collection_name)
        return {"message": f"Collection '{collection_name}' created successfully in database '{db_name}'."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Errore nella creazione della collezione: {str(e)}"
        )


@app.get("/{db_name}/list_collections/", summary="Elenca le collezioni in un database",
         response_description="Elenco delle collezioni presenti nel database")
async def list_collections(db_name: str):
    try:
        db = get_db_instance(db_name)
    except Exception:
        db = await add_database(db_name)
    try:
        collection_list = await db.list_collection_names()
        return {"collections": collection_list}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Errore nel recupero delle collezioni: {str(e)}"
        )


@app.delete("/{db_name}/delete_collection/{collection_name}/", summary="Elimina una collezione esistente",
            response_description="La collezione è stata eliminata con successo")
async def delete_collection(db_name: str, collection_name: str):
    try:
        db = get_db_instance(db_name)
        await db.drop_collection(collection_name)
        return {"message": f"Collection '{collection_name}' deleted successfully from database '{db_name}'."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Errore nell'eliminazione della collezione: {str(e)}"
        )


@app.post("/upload_schema/{db_name}/{collection_name}/",
          summary="Carica uno o più schemi YAML per una collezione specifica")
async def upload_schema(db_name: str, collection_name: str, files: List[UploadFile] = File(...)):
    try:
        schema_dir = os.path.join("allowed_schemas", db_name, collection_name)
        os.makedirs(schema_dir, exist_ok=True)
        for file in files:
            content = await file.read()
            schema = yaml.safe_load(content)
            schema_path = os.path.join(schema_dir, file.filename)
            with open(schema_path, "w") as schema_file:
                yaml.dump(schema, schema_file)
            schema_key = f"{db_name}/{collection_name}/{file.filename}"
            schemas[schema_key] = schema
        return {
            "message": f"Schemi per la collezione '{collection_name}' nel database '{db_name}' caricati con successo."
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Errore durante il caricamento degli schemi: {str(e)}"
        )


@app.post("/{db_name}/{collection_name}/add_item/",
          summary="Aggiungi un documento in una collezione convalidato tramite schema specifico")
async def add_item(db_name: str, collection_name: str, data: Dict[str, Any]):
    try:
        db = get_db_instance(db_name)
    except Exception:
        db = await add_database(db_name)
    try:
        if DATA_VALIDATION:
            validated_data = validate_input(db_name, collection_name, data)
            data = validated_data
        collection = db[collection_name]
        result = await collection.insert_one(data)
        return {"message": "Item added successfully.", "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Errore nell'aggiunta del documento: {str(e)}"
        )


@app.post("/{db_name}/get_items/{collection_name}/", summary="Recupera tutti i documenti di una collezione",
          response_description="Elenco dei documenti nella collezione", response_model=List[Dict[str, Any]])
async def get_items(db_name: str, collection_name: str, filter: Optional[Dict[str, Any]] = Body(None)):
    try:
        db = get_db_instance(db_name)
    except Exception:
        db = await add_database(db_name)
    query = filter if filter else {}
    try:
        collection = db[collection_name]
        items = []
        async for item in collection.find(query):
            item["_id"] = str(item["_id"])
            items.append(item)
        return items
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Errore nel recupero dei documenti: {str(e)}"
        )


@app.put("/{db_name}/update_item/{collection_name}/{item_id}/", summary="Aggiorna un documento in una collezione",
         response_description="Il documento è stato aggiornato con successo")
async def update_item(db_name: str, collection_name: str, item_id: str, item: Dict[str, Any]):
    try:
        db = get_db_instance(db_name)
    except Exception:
        db = await add_database(db_name)
    try:
        collection = db[collection_name]
        result = await collection.update_one({"_id": ObjectId(item_id)}, {"$set": item})
        if result.modified_count:
            return {"message": "Item updated successfully."}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nessun documento aggiornato."
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Errore nell'aggiornamento del documento: {str(e)}"
        )


@app.delete("/{db_name}/delete_item/{collection_name}/{item_id}/", summary="Elimina un documento in una collezione",
            response_description="Il documento è stato eliminato con successo")
async def delete_item(db_name: str, collection_name: str, item_id: str):
    try:
        db = get_db_instance(db_name)
    except Exception:
        db = await add_database(db_name)
    try:
        collection = db[collection_name]
        result = await collection.delete_one({"_id": ObjectId(item_id)})
        if result.deleted_count:
            return {"message": "Item deleted successfully."}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento non trovato."
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Errore nell'eliminazione del documento: {str(e)}"
        )


@app.get("/{db_name}/get_item/{collection_name}/{item_id}/", summary="Recupera un documento specifico",
         response_description="Il documento è stato recuperato con successo", response_model=Dict[str, Any])
async def get_item(db_name: str, collection_name: str, item_id: str):
    try:
        db = get_db_instance(db_name)
    except Exception:
        db = await add_database(db_name)
    try:
        collection = db[collection_name]
        item = await collection.find_one({"_id": ObjectId(item_id)})
        if item:
            item["_id"] = str(item["_id"])
            return item
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento non trovato."
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Errore nel recupero del documento: {str(e)}"
        )


@app.get("/get_schemas/{db_name}/{collection_name}/", summary="Visualizza gli schemi associati a una collezione",
         response_description="Elenco degli schemi YAML per la collezione specificata")
async def get_schemas(db_name: str, collection_name: str):
    try:
        schema_dir = os.path.join("allowed_schemas", db_name, collection_name)
        if not os.path.exists(schema_dir):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nessuno schema trovato per questa collezione e database."
            )
        schema_files = os.listdir(schema_dir)
        if not schema_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nessuno schema trovato per questa collezione e database."
            )
        schemas_content = {}
        for schema_file in schema_files:
            schema_path = os.path.join(schema_dir, schema_file)
            with open(schema_path, "r") as f:
                schema_content = yaml.safe_load(f)
                schemas_content[schema_file] = schema_content
        return {"schemas": schemas_content}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Errore nel recupero degli schemi: {str(e)}"
        )


@app.post("/{db_name}/{collection_name}/search", summary="Ricerca documenti con filtro e paginazione",
          response_description="Risultati della ricerca con parametri di paginazione")
async def search_documents(
        db_name: str,
        collection_name: str,
        filter: Optional[Dict[str, Any]] = Body(default={}, description="Filtro per la ricerca dei documenti"),
        skip: int = 0,
        size: int = 10
):
    try:
        try:
            db = get_db_instance(db_name)
        except Exception:
            db = await add_database(db_name)
        collection = db[collection_name]
        query = filter if filter is not None else {}
        items = []
        cursor = collection.find(query).skip(skip).limit(size)
        async for item in cursor:
            item["_id"] = str(item["_id"])
            items.append(item)
        return {
            "results": items,
            "pagination": {
                "skip": skip,
                "size": size,
                "returned_count": len(items)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Errore nella ricerca dei documenti: {str(e)}"
        )
