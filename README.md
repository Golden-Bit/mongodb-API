# Documentazione API – MongoDB FastAPI Backend

**Versione:** 1.0.0  
**Base URL:**  
```
https://<your-domain>/mongodb-api
```

Questa API consente di gestire in maniera asincrona database, collezioni e documenti su MongoDB Atlas. Utilizza il driver asincrono **Motor** configurato con il Server API v1 per garantire la compatibilità con le versioni stabili del cluster Atlas.

---

## Indice
1. [Creare un Database](#creare-un-database)
2. [Elencare i Database](#elencare-i-database)
3. [Eliminare un Database](#eliminare-un-database)
4. [Creare una Collezione](#creare-una-collezione)
5. [Elencare le Collezioni](#elencare-le-collezioni)
6. [Eliminare una Collezione](#eliminare-una-collezione)
7. [Caricare Schemi YAML](#caricare-schemi-yaml)
8. [Inserire un Documento (Add Item)](#inserire-un-documento-add-item)
9. [Recuperare Documenti (Get Items)](#recuperare-documenti-get-items)
10. [Aggiornare un Documento](#aggiornare-un-documento)
11. [Eliminare un Documento](#eliminare-un-documento)
12. [Recuperare un Documento Specifico](#recuperare-un-documento-specifico)
13. [Recuperare Schemi](#recuperare-schemi)
14. [Ricerca Documenti con Pagina­zione](#ricerca-documenti-con-paginazione)

---

## 1. Creare un Database

**Endpoint:**  
```
POST /create_database/
```

**Descrizione:**  
Crea (e connette) un nuovo database. In MongoDB il database viene creato in modalità _lazy_ (quando viene inserito il primo documento), ma questo endpoint stabilisce la connessione e memorizza l’istanza nel cache.

**Input (Request Body – JSON):**
```json
{
  "db_name": "myDatabase",
  "username": "admin",
  "password": "password123",
  "host": "mongodb",
  "port": 27017
}
```

**Dettagli dei campi:**
- **db_name (string):** Nome del database.
- **username (string, opzionale):** Nome utente per l’autenticazione.
- **password (string, opzionale):** Password dell’utente.
- **host (string, opzionale):** Host del database (in ambiente Atlas, la configurazione avviene nella URI).
- **port (integer, opzionale):** Porta del database (default 27017).

**Output (Response):**
- **Successo (200):**
  ```json
  {
    "message": "Database 'myDatabase' created and connected successfully."
  }
  ```
- **Errore (400):**
  ```json
  {
    "detail": "Errore nella creazione del database: <error details>"
  }
  ```

**Esempio di richiesta (curl):**
```bash
curl -X POST "https://your-domain/mongodb-api/create_database/" \
     -H "Content-Type: application/json" \
     -d '{
           "db_name": "myDatabase",
           "username": "admin",
           "password": "password123",
           "host": "mongodb",
           "port": 27017
         }'
```

---

## 2. Elencare i Database

**Endpoint:**  
```
GET /list_databases/
```

**Descrizione:**  
Recupera la lista di tutti i database disponibili sul server MongoDB.

**Output (Response):**
- **Successo (200):**
  ```json
  {
    "databases": ["admin", "local", "myDatabase", "anotherDB"]
  }
  ```
- **Errore (400):**
  ```json
  {
    "detail": "Errore nel recupero dei database: <error details>"
  }
  ```

**Esempio di richiesta (curl):**
```bash
curl -X GET "https://your-domain/mongodb-api/list_databases/"
```

---

## 3. Eliminare un Database

**Endpoint:**  
```
DELETE /delete_database/{db_name}/
```

**Descrizione:**  
Elimina il database specificato e rimuove l’istanza dal cache.

**Path Parameter:**
- **db_name (string):** Nome del database da eliminare.

**Output (Response):**
- **Successo (200):**
  ```json
  {
    "message": "Database 'myDatabase' deleted successfully."
  }
  ```
- **Errore (400):**
  ```json
  {
    "detail": "Errore nell'eliminazione del database: <error details>"
  }
  ```

**Esempio di richiesta (curl):**
```bash
curl -X DELETE "https://your-domain/mongodb-api/delete_database/myDatabase/"
```

---

## 4. Creare una Collezione

**Endpoint:**  
```
POST /{db_name}/create_collection/
```

**Descrizione:**  
Crea una nuova collezione all’interno del database specificato.

**Path Parameter:**
- **db_name (string):** Nome del database.

**Query Parameter:**
- **collection_name (string):** Nome della collezione da creare.

**Output (Response):**
- **Successo (200):**
  ```json
  {
    "message": "Collection 'myCollection' created successfully in database 'myDatabase'."
  }
  ```
- **Errore (400):**
  ```json
  {
    "detail": "Errore nella creazione della collezione: <error details>"
  }
  ```

**Esempio di richiesta (curl):**
```bash
curl -X POST "https://your-domain/mongodb-api/myDatabase/create_collection/?collection_name=myCollection"
```

---

## 5. Elencare le Collezioni

**Endpoint:**  
```
GET /{db_name}/list_collections/
```

**Descrizione:**  
Recupera l’elenco delle collezioni presenti nel database specificato.

**Path Parameter:**
- **db_name (string):** Nome del database.

**Output (Response):**
- **Successo (200):**
  ```json
  {
    "collections": ["myCollection", "anotherCollection"]
  }
  ```
- **Errore (400):**
  ```json
  {
    "detail": "Errore nel recupero delle collezioni: <error details>"
  }
  ```

**Esempio di richiesta (curl):**
```bash
curl -X GET "https://your-domain/mongodb-api/myDatabase/list_collections/"
```

---

## 6. Eliminare una Collezione

**Endpoint:**  
```
DELETE /{db_name}/delete_collection/{collection_name}/
```

**Descrizione:**  
Elimina la collezione specificata dal database.

**Path Parameters:**
- **db_name (string):** Nome del database.
- **collection_name (string):** Nome della collezione da eliminare.

**Output (Response):**
- **Successo (200):**
  ```json
  {
    "message": "Collection 'myCollection' deleted successfully from database 'myDatabase'."
  }
  ```
- **Errore (400):**
  ```json
  {
    "detail": "Errore nell'eliminazione della collezione: <error details>"
  }
  ```

**Esempio di richiesta (curl):**
```bash
curl -X DELETE "https://your-domain/mongodb-api/myDatabase/delete_collection/myCollection/"
```

---

## 7. Caricare Schemi YAML

**Endpoint:**  
```
POST /upload_schema/{db_name}/{collection_name}/
```

**Descrizione:**  
Carica uno o più file YAML che definiscono gli schemi di validazione per i documenti di una specifica collezione. I file vengono salvati in `allowed_schemas/{db_name}/{collection_name}/` e usati per validare i dati in ingresso (se attivata la validazione).

**Path Parameters:**
- **db_name (string):** Nome del database.
- **collection_name (string):** Nome della collezione.

**Form Data:**
- **files:** Uno o più file YAML (multipart/form-data).

**Output (Response):**
- **Successo (200):**
  ```json
  {
    "message": "Schemi per la collezione 'myCollection' nel database 'myDatabase' caricati con successo."
  }
  ```
- **Errore (400):**
  ```json
  {
    "detail": "Errore durante il caricamento degli schemi: <error details>"
  }
  ```

**Esempio di richiesta (curl):**
```bash
curl -X POST "https://your-domain/mongodb-api/upload_schema/myDatabase/myCollection/" \
     -F "files=@schema.yaml"
```

---

## 8. Inserire un Documento (Add Item)

**Endpoint:**  
```
POST /{db_name}/{collection_name}/add_item/
```

**Descrizione:**  
Inserisce un nuovo documento nella collezione specificata. Se attivata la validazione dei dati (flag `DATA_VALIDATION`), il documento viene validato contro gli schemi YAML associati.

**Path Parameters:**
- **db_name (string):** Nome del database.
- **collection_name (string):** Nome della collezione.

**Request Body (JSON):**
```json
{
  "field1": "exampleValue",
  "field2": 42
}
```

**Output (Response):**
- **Successo (200):**
  ```json
  {
    "message": "Item added successfully.",
    "id": "60c5ba8e1d4a2c3a4f5b6d7e"
  }
  ```
- **Errore (400):**
  ```json
  {
    "detail": "Errore nell'aggiunta del documento: <error details>"
  }
  ```

**Esempio di richiesta (curl):**
```bash
curl -X POST "https://your-domain/mongodb-api/myDatabase/myCollection/add_item/" \
     -H "Content-Type: application/json" \
     -d '{"field1": "exampleValue", "field2": 42}'
```

---

## 9. Recuperare Documenti (Get Items)

**Endpoint:**  
```
POST /{db_name}/get_items/{collection_name}/
```

**Descrizione:**  
Recupera tutti i documenti presenti nella collezione. È possibile passare un filtro (query) nel body per limitare i risultati.

**Path Parameters:**
- **db_name (string):** Nome del database.
- **collection_name (string):** Nome della collezione.

**Request Body (JSON, opzionale):**
- Se non specificato, viene utilizzato un filtro vuoto `{}`.
  
Esempio di payload (con filtro):
```json
{
  "field1": "exampleValue"
}
```

**Output (Response):**
- **Successo (200):**
  ```json
  [
    {
      "_id": "60c5ba8e1d4a2c3a4f5b6d7e",
      "field1": "exampleValue",
      "field2": 42
    },
    ...
  ]
  ```
- **Errore (400):**
  ```json
  {
    "detail": "Errore nel recupero dei documenti: <error details>"
  }
  ```

**Esempio di richiesta (curl):**
```bash
curl -X POST "https://your-domain/mongodb-api/myDatabase/get_items/myCollection/" \
     -H "Content-Type: application/json" \
     -d '{"field1": "exampleValue"}'
```

---

## 10. Aggiornare un Documento

**Endpoint:**  
```
PUT /{db_name}/update_item/{collection_name}/{item_id}/
```

**Descrizione:**  
Aggiorna un documento esistente nella collezione. Il documento viene identificato dal suo ID (MongoDB ObjectId).

**Path Parameters:**
- **db_name (string):** Nome del database.
- **collection_name (string):** Nome della collezione.
- **item_id (string):** ID del documento da aggiornare.

**Request Body (JSON):**
Esempio di payload:
```json
{
  "field2": 100
}
```

**Output (Response):**
- **Successo (200):**
  ```json
  {
    "message": "Item updated successfully."
  }
  ```
- **Errore (404):**
  ```json
  {
    "detail": "Nessun documento aggiornato."
  }
  ```
- **Errore (400):**
  ```json
  {
    "detail": "Errore nell'aggiornamento del documento: <error details>"
  }
  ```

**Esempio di richiesta (curl):**
```bash
curl -X PUT "https://your-domain/mongodb-api/myDatabase/update_item/myCollection/60c5ba8e1d4a2c3a4f5b6d7e/" \
     -H "Content-Type: application/json" \
     -d '{"field2": 100}'
```

---

## 11. Eliminare un Documento

**Endpoint:**  
```
DELETE /{db_name}/delete_item/{collection_name}/{item_id}/
```

**Descrizione:**  
Elimina il documento identificato dall’ID dalla collezione specificata.

**Path Parameters:**
- **db_name (string):** Nome del database.
- **collection_name (string):** Nome della collezione.
- **item_id (string):** ID del documento da eliminare.

**Output (Response):**
- **Successo (200):**
  ```json
  {
    "message": "Item deleted successfully."
  }
  ```
- **Errore (404):**
  ```json
  {
    "detail": "Documento non trovato."
  }
  ```
- **Errore (400):**
  ```json
  {
    "detail": "Errore nell'eliminazione del documento: <error details>"
  }
  ```

**Esempio di richiesta (curl):**
```bash
curl -X DELETE "https://your-domain/mongodb-api/myDatabase/delete_item/myCollection/60c5ba8e1d4a2c3a4f5b6d7e/"
```

---

## 12. Recuperare un Documento Specifico

**Endpoint:**  
```
GET /{db_name}/get_item/{collection_name}/{item_id}/
```

**Descrizione:**  
Recupera un singolo documento identificato dal suo ID.

**Path Parameters:**
- **db_name (string):** Nome del database.
- **collection_name (string):** Nome della collezione.
- **item_id (string):** ID del documento da recuperare.

**Output (Response):**
- **Successo (200):**
  ```json
  {
    "_id": "60c5ba8e1d4a2c3a4f5b6d7e",
    "field1": "exampleValue",
    "field2": 100
  }
  ```
- **Errore (404):**
  ```json
  {
    "detail": "Documento non trovato."
  }
  ```
- **Errore (400):**
  ```json
  {
    "detail": "Errore nel recupero del documento: <error details>"
  }
  ```

**Esempio di richiesta (curl):**
```bash
curl -X GET "https://your-domain/mongodb-api/myDatabase/get_item/myCollection/60c5ba8e1d4a2c3a4f5b6d7e/"
```

---

## 13. Recuperare Schemi

**Endpoint:**  
```
GET /get_schemas/{db_name}/{collection_name}/
```

**Descrizione:**  
Recupera tutti i file YAML che definiscono gli schemi di validazione per la collezione, memorizzati nel percorso `allowed_schemas/{db_name}/{collection_name}/`.

**Path Parameters:**
- **db_name (string):** Nome del database.
- **collection_name (string):** Nome della collezione.

**Output (Response):**
- **Successo (200):**
  ```json
  {
    "schemas": {
      "schema1.yaml": { ... contenuto dello schema ... },
      "schema2.yaml": { ... contenuto dello schema ... }
    }
  }
  ```
- **Errore (404):**
  ```json
  {
    "detail": "Nessuno schema trovato per questa collezione e database."
  }
  ```
- **Errore (400):**
  ```json
  {
    "detail": "Errore nel recupero degli schemi: <error details>"
  }
  ```

**Esempio di richiesta (curl):**
```bash
curl -X GET "https://your-domain/mongodb-api/get_schemas/myDatabase/myCollection/"
```

---

## 14. Ricerca Documenti con Paginazione

**Endpoint:**  
```
POST /{db_name}/{collection_name}/search
```

**Descrizione:**  
Esegue una ricerca nella collezione specificata applicando un filtro e utilizzando parametri di paginazione (skip e size).

**Path Parameters:**
- **db_name (string):** Nome del database.
- **collection_name (string):** Nome della collezione.

**Request Body (JSON):**
```json
{
  "filter": { "field1": "exampleValue" },
  "skip": 0,
  "size": 10
}
```

**Dettagli dei campi:**
- **filter (object, opzionale):** Query di ricerca in formato MongoDB.
- **skip (integer, opzionale):** Numero di documenti da saltare (default 0).
- **size (integer, opzionale):** Numero massimo di documenti da restituire (default 10).

**Output (Response):**
- **Successo (200):**
  ```json
  {
    "results": [
      { "_id": "60c5ba8e1d4a2c3a4f5b6d7e", "field1": "exampleValue", "field2": 42 },
      ...
    ],
    "pagination": {
      "skip": 0,
      "size": 10,
      "returned_count": 1
    }
  }
  ```
- **Errore (400):**
  ```json
  {
    "detail": "Errore nella ricerca dei documenti: <error details>"
  }
  ```

**Esempio di richiesta (curl):**
```bash
curl -X POST "https://your-domain/mongodb-api/myDatabase/myCollection/search" \
     -H "Content-Type: application/json" \
     -d '{
           "filter": { "field1": "exampleValue" },
           "skip": 0,
           "size": 10
         }'
```

---