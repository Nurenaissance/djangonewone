from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import IntegrityError, connection
from rest_framework import status
from rest_framework.response import Response
import os, pymupdf, json, io, pdfplumber, asyncio
from openai import OpenAI
import numpy as np, psycopg2
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain_community.embeddings import OpenAIEmbeddings
from analytics.models import userData, FAISSIndex
from psycopg2 import sql
from .tables import get_db_connection

# Initialize OpenAI client lazily to avoid import-time errors in test/CI
_client = None

def get_openai_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client

# Database connection string
DB_CONNECTION_STRING = 'postgresql://nurenai:Biz1nurenWar*@nurenaistore.postgres.database.azure.com:5432/nurenpostgres'

def whatsapp_prompts(required_fields, type):
    """Generate prompts for WhatsApp media processing"""
    PROMPT_FOR_IMAGE = f"""
    identify the fields: {required_fields} from the following image.
    return the answer in json format. if any of the field is missing, return null in its place

    if you dont know the answer, return an empty json object. dont include any apologies or any other statements in your response
    """

    PROMPT_FOR_DOC = f"""
    identify the fields: {required_fields} from the following text.
    return the answer in json format. if any of the field is missing, return null in its place

    if you dont know the answer, return an empty json object. dont include any apologies or any other statements in your response
    """

    if type == "image":
        return PROMPT_FOR_IMAGE
    elif type == "doc":
        return PROMPT_FOR_DOC
    else:
        return ""

def split_file(pdf_file, chunk_size=100, chunk_overlap=30): 
    """Split PDF file into chunks"""
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        document = pymupdf.open(stream=pdf_file, filetype="pdf")
        full_text = ""
        for page_num in range(len(document)):
            page = document.load_page(page_num)
            full_text += page.get_text()

        texts = text_splitter.split_text(full_text)
        return texts
    except Exception as e:
        print(f"Error splitting file: {e}")
        return []

def get_embeddings(chunks):
    """Generate embeddings for text chunks"""
    embeddings = []
    try:
        for chunk in chunks:
            response = get_openai_client().embeddings.create(input=chunk, model="text-embedding-3-small")
            embeddings.append(response.data[0].embedding)
            print("chunk processed")
        print("Successfully created embeddings out of chunks")
        return embeddings
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return []

def vectorize(pdf_file):
    """Vectorize PDF file and store in database"""
    try:
        print("Entering Vectorize...")
        chunks = split_file(pdf_file)
        if not chunks:
            return JsonResponse({"status": 400, "message": "Failed to extract text from PDF"}, status=400)
        
        print("chunks created")
        embeddings = get_embeddings(chunks)
        if not embeddings:
            return JsonResponse({"status": 500, "message": "Failed to generate embeddings"}, status=500)
        
        print("embeddings created")

        with connection.cursor() as cursor:
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS text_embeddings (
                id SERIAL PRIMARY KEY,
                chunk TEXT,
                embedding vector(1536)
            )
            ''')
        connection.commit()

        # Insert embeddings into the table
        for i, chunk in enumerate(chunks):
            embedding_array = np.array(embeddings[i])
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO text_embeddings (chunk, embedding) VALUES (%s, %s::vector)",
                    (chunk, embedding_array.tolist())
                )
        connection.commit()
        print("Text Vectorized Successfully")
        return JsonResponse({"status": 200, "message": "Text vectorized successfully"})

    except Exception as e:
        print(f"An error occurred: {e}")
        return JsonResponse({"status": 500, "message": f"An error occurred: {e}"}, status=500)

def process_chunks(chunks):
    """Process chunks and store embeddings"""
    try:
        embeddings = get_embeddings(chunks)
        if not embeddings:
            return False

        with connection.cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS text_embeddings (
                    id SERIAL PRIMARY KEY,
                    chunk TEXT,
                    embedding vector(1536)
                )
            ''')
        connection.commit()

        # Insert embeddings into the table
        for i, chunk in enumerate(chunks):
            embedding_array = np.array(embeddings[i])
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO text_embeddings (chunk, embedding) VALUES (%s, %s::vector)",
                    (chunk, embedding_array.tolist())
                )
        connection.commit()
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def get_query_embedding(query):
    """Get embedding for query text"""
    try:
        response = get_openai_client().embeddings.create(
            input=query,
            model="text-embedding-ada-002"
        )
        embedding = response.data[0].embedding
        return embedding
    except Exception as e:
        print(f"Error getting query embedding: {e}")
        return None

def store_chunk_embedding(chunk, embedding):
    """Store chunk embedding in database"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO text_embeddings (chunk, embedding) VALUES (%s, %s::vector(1536))",
                (chunk, embedding)
            )
        connection.commit()
    except Exception as e:
        print(f"Error storing chunk embedding: {e}")
    return []

def perform_cosine_similarity_search(query_embedding):
    """Perform cosine similarity search using pgvector"""
    try:
        query_embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        print("Query embedding string: ", query_embedding_str)
        
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    te.id,
                    te.chunk AS most_similar_chunk,
                    (te.embedding::vector) <=> %s AS similarity_score
                FROM
                    text_embeddings te
                ORDER BY (te.embedding::vector) <=> %s DESC
                LIMIT 10;
                """,
                [query_embedding_str, query_embedding_str]
            )
            results = cursor.fetchall()
            return results
    except Exception as e:
        print(f"Error in similarity search: {e}")
        return []

def process_and_search_similar_queries(query):
    """Main function to process and search similar queries"""
    try:
        query_embedding = get_query_embedding(query)
        if not query_embedding:
            return []
        
        query_embedding_array = np.array(query_embedding, dtype=np.float64)
        similar_queries = perform_cosine_similarity_search(query_embedding_array)
        print("similar queries: ", similar_queries)
        return similar_queries
    except Exception as e:
        print(f"Error processing and searching queries: {e}")
        return []

async def get_relevant_node_id(query_string, nodes):
    """Helper function for the first OpenAI API call"""
    try:
        response = await asyncio.to_thread(
            get_openai_client().chat.completions.create,
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an intelligent assistant. You will receive a user query and a list of nodes. Each node contains an `id` and a `description` of text. Your task is to determine whether any node contains relevant information that directly answers the user's query. If one does, return ONLY the `id` of the most relevant node. If none of the nodes contain relevant information, return -1. IMPORTANT: Only return the raw id (like 4 or -1). Do not include any explanation, markdown, or quotes"},
                {"role": "user", "content": f"User Query: {query_string}"},
                {"role": "user", "content": f"Nodes: {nodes}"}
            ]
        )
        return response.choices[0].message.content, None
    except Exception as e:
        return None, str(e)

async def get_openai_response(query_string, combined_query, userJSON_serialized, language, prompt):
    """Helper function for the second OpenAI API call"""
    try:
        response = await asyncio.to_thread(
            get_openai_client().chat.completions.create,
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"you shall answer the queries asked based on the following text provided: {combined_query}. Try to include all the details and names. Make it as descriptive as possible but take inputs only from the text provided."},
                {"role": "user", "content": f"please omit any apostrophes or inverted commas in your response. Personalize your response. greet with name. use these details: {userJSON_serialized}"},
                {"role": "user", "content": f"Respond in proper {language} language specifically. Use the alphabet of this specific language and its alphabet only(like for Hindi use proper Devnagri script)."},
                {"role": "user", "content": query_string}
            ]
        )
        return response.choices[0].message.content, None
    except Exception as e:           
        return None, str(e)

def get_similar_chunks_using_faiss(query, userJSON, name):
    """Get similar chunks using FAISS"""
    try:
        print("Name: ", name)
        
        # Fetch the index data from FAISSIndex model
        index_data = FAISSIndex.objects.get(name=name)
        
        # Deserialize FAISS index
        embeddings = OpenAIEmbeddings()
        library = FAISS.deserialize_from_bytes(
            index_data.index_data, 
            embeddings, 
            allow_dangerous_deserialization=True
        )

        print("FAISS library created.")
        
        # Combine the query and userJSON data
        combined_query = query + json.dumps(userJSON)

        # Perform similarity search
        answer = library.similarity_search(combined_query)
        print(f"Answer retrieved: {answer}")
        
        return answer

    except ObjectDoesNotExist:
        print("Error: FAISS index not found.")
        return None
    except ValueError as e:
        print(f"Error in FAISS deserialization: {str(e)}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return None

@csrf_exempt
def query(request):
    """Main query endpoint"""
    try:
        tenant_id = request.headers.get('X-Tenant-Id')
        if not tenant_id:
            return JsonResponse({"data": {"status": 400, "message": "Tenant ID is required."}}, status=400)
            
        req_body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"data": {"status": 400, "message": "Invalid JSON body."}}, status=400)
    
    query_string = req_body.get("query", "")
    phone = req_body.get("phone")
    nodes = req_body.get("nodes", [])
    language = req_body.get("language", "English")
    
    if not query_string:
        return JsonResponse({"data": {"status": 400, "message": "Query is required."}}, status=400)
    
    try:
        userJSON = userData.objects.filter(tenant_id=tenant_id, phone=phone)
        faiss_index = FAISSIndex.objects.get(tenant_id=tenant_id)
        doc_name = faiss_index.name
    except ObjectDoesNotExist:
        return JsonResponse({"data": {"status": 404, "message": "FAISS index not found for tenant."}}, status=404)
    except Exception as e:
        return JsonResponse({"data": {"status": 500, "message": f"Database error: {str(e)}"}}, status=500)
    
    userJSON_list = list(userJSON.values())
    userJSON_serialized = json.dumps(userJSON_list)
    
    print("user json: ", userJSON_serialized)
    print("query string: ", query_string)
    print("Name: ", doc_name)
    
    try:
        similar_chunks = get_similar_chunks_using_faiss(query_string, userJSON_serialized, doc_name)
    except Exception as e:
        return JsonResponse({"data": {"status": 500, "message": f"FAISS search error: {str(e)}"}}, status=500)
    
    # Define the prompt
    prompt = "You are a helpful assistant that answers queries based on provided text."
    
    # Run API calls in parallel
    async def run_parallel_calls():
        node_id_task = get_relevant_node_id(query_string, nodes)
        
        if similar_chunks:
            combined_query = " ".join([doc.page_content for doc in similar_chunks])
            openai_response_task = get_openai_response(query_string, combined_query, userJSON_serialized, language, prompt)
            
            (node_id, node_id_error), (openai_response, openai_error) = await asyncio.gather(
                node_id_task, openai_response_task, return_exceptions=True
            )
            return node_id, node_id_error, openai_response, openai_error
        else:
            node_id, node_id_error = await node_id_task
            return node_id, node_id_error, None, "No similar chunks found"
    
    try:
        node_id, node_id_error, openai_response, openai_error = asyncio.run(run_parallel_calls())
        
        # Handle errors from async calls
        if node_id_error:
            return JsonResponse({"data": {"status": 500, "message": f"Node ID error: {node_id_error}"}}, status=500)
        
        if openai_error and openai_error != "No similar chunks found":
            return JsonResponse({"data": {"status": 500, "message": f"OpenAI error: {openai_error}"}}, status=500)
        
        return JsonResponse({
            "status": 200, 
            "message": openai_response or "No relevant information found.", 
            "id": node_id
        })
        
    except Exception as e:
        return JsonResponse({"data": {"status": 500, "message": f"Async execution error: {str(e)}"}}, status=500)

def get_docs():
    """Get all document chunks from database"""
    try:
        query = "SELECT chunk from text_embeddings"
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
        
        # Extract chunks from the result
        chunks = [row[0] for row in result]
        return chunks
    except Exception as e:
        print(f"Error getting docs: {e}")
        return []

@csrf_exempt
def vectorize_FAISS(pdf_file, file_name, json_data, tenant_id):
    """Vectorize PDF using FAISS and store in database"""
    name = file_name
    print("File name:", name)
    
    try:
        # Determine chunk size based on PDF page count
        with pymupdf.open(stream=pdf_file, filetype="pdf") as pdf_document:
            num_pages = pdf_document.page_count
            print(f"The PDF has {num_pages} pages.")

            if num_pages < 40:
                chunk_size = 100
                chunk_overlap = 20
            elif 40 <= num_pages <= 99:
                chunk_size = 300
                chunk_overlap = 50
            elif 100 <= num_pages < 200:
                chunk_size = 600
                chunk_overlap = 70
            else:  # num_pages >= 200
                chunk_size = 1000
                chunk_overlap = 100

        chunks = split_file(pdf_file, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        if not chunks:
            return JsonResponse({"status": 400, "message": "Failed to extract text from PDF"}, status=400)
        
        doc_objects = [Document(page_content=chunk) for chunk in chunks]

        # Create embeddings
        embedding = OpenAIEmbeddings()
        print("Embeddings created.")

        try:
            # Check for existing FAISS index by tenant_id
            existing_faiss_index = FAISSIndex.objects.get(tenant_id=tenant_id)
            print("Existing FAISS index found for tenant. Replacing it with new data.")
            
            # Create a new FAISS index with the new documents
            library = FAISS.from_documents(doc_objects, embedding)
            print("Library created")
            
            # Serialize the new index to bytes
            serialized_index = library.serialize_to_bytes()
            print("Index serialized")
            
            # Replace the old data with new data
            existing_faiss_index.name = name
            existing_faiss_index.index_data = serialized_index
            existing_faiss_index.json_data = json_data
            existing_faiss_index.save()
            print("Existing FAISS index replaced with new data.")

        except ObjectDoesNotExist:
            # No FAISS index found, create a new one
            print("No FAISS index found for the tenant. Creating a new one.")
            
            library = FAISS.from_documents(doc_objects, embedding)
            serialized_index = library.serialize_to_bytes()
            
            faiss_index = FAISSIndex(
                name=name,
                index_data=serialized_index,
                json_data=json_data,
                tenant_id=tenant_id
            )
            faiss_index.save()
            print("New FAISS index saved.")

        except IntegrityError as e:
            return JsonResponse({"status": 500, "error": "Database error", "message": str(e)}, status=500)
        except Exception as e:
            return JsonResponse({"status": 500, "error": "FAISS index error", "message": str(e)}, status=500)
        
    except FileNotFoundError:
        return JsonResponse({"status": 404, "error": "File not found", "message": f"PDF file '{name}' not found."}, status=404)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return JsonResponse({"status": 500, "error": "Unexpected error", "message": str(e)}, status=500)

    return JsonResponse({"status": 200, "message": "Text vectorized successfully"})

@csrf_exempt
def handle_media_uploads(request):
    """Handle media uploads for WhatsApp"""
    if request.method == 'POST':
        try:
            print("Received request: ", request)

            tenant_id = request.headers.get('X-Tenant-Id')
            if not tenant_id:
                return JsonResponse({"error": "Tenant ID is required."}, status=400)
            
            user_data = request.headers.get('user-data')
            if not user_data:
                return JsonResponse({"error": "User data is required."}, status=400)
            
            print("user data: ", user_data)
            user_data = json.loads(user_data)
            user_data['tenant_id'] = tenant_id
            
            try:
                existing_faiss_index = FAISSIndex.objects.get(tenant_id=tenant_id)
                required_fields = list(json.loads(existing_faiss_index.json_data).values())
            except ObjectDoesNotExist:
                return JsonResponse({"error": "FAISS index not found for tenant."}, status=404)
            except Exception as e:
                return JsonResponse({"error": f"Database error: {str(e)}"}, status=500)
            
            print("Required fields: ", required_fields)
            files = request.FILES

            if not files:
                # Handle image processing
                prompt = whatsapp_prompts(required_fields=required_fields, type="image")
                data = json.loads(request.body)
                image_buffer = data.get('image_buffer')
                
                if not image_buffer:
                    return JsonResponse({"error": "No image buffer provided."}, status=400)

                content = [
                    {
                        'type': "text",
                        'text': prompt
                    },
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f"data:image/webp;base64,{image_buffer}"
                        }
                    }
                ]
            else:
                # Handle document processing
                prompt = whatsapp_prompts(required_fields=required_fields, type="doc")
                pdf_file = request.FILES.get('pdf')

                if not pdf_file:
                    return JsonResponse({"error": "No PDF file received."}, status=400)

                try:
                    pdf_stream = io.BytesIO(pdf_file.read())
                    extracted_text = ''
                    
                    with pdfplumber.open(pdf_stream) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                extracted_text += page_text
                    
                    if not extracted_text:
                        return JsonResponse({"error": "No text could be extracted from PDF."}, status=400)
                    
                except Exception as e:
                    return JsonResponse({"error": f"Error processing PDF: {str(e)}"}, status=500)
                
                content = [
                    {
                        'type': "text",
                        'text': prompt
                    },
                    {
                        'type': 'text',
                        'text': extracted_text
                    }
                ]
            
            print("CONTENT: ", content)
            
            try:
                response = get_openai_client().chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            'role': "user",
                            'content': content
                        }
                    ]
                )

                if response.choices:
                    answer = response.choices[0].message.content
                    start_index = answer.find('{')
                    end_index = answer.rfind('}') + 1
                    
                    if start_index != -1 and end_index > start_index:
                        answer = answer[start_index:end_index].strip()
                        answer = json.loads(answer)
                    else:
                        return JsonResponse({"error": "No valid JSON found in response."}, status=500)
                else:
                    return JsonResponse({"error": "No response from the model."}, status=500)
            
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON response from model."}, status=500)
            except Exception as e:
                return JsonResponse({"error": f"OpenAI API error: {str(e)}"}, status=500)
            
            user_data['data'] = answer
            print("JSON response: ", user_data)

            return JsonResponse({"success": answer})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON in request body."}, status=400)
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"error": "Error processing the request."}, status=500)

    return JsonResponse({"error": "Invalid request method. Use POST."}, status=405)

def get_embedding(text, model="text-embedding-ada-002"):
    """Get embedding for text"""
    try:
        text = text.replace("\n", " ")
        return get_openai_client().embeddings.create(input=[text], model=model).data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None

def find_similar_embeddings(query_embedding, threshold=0.5):
    """Find similar embeddings in database"""
    try:
        conn = psycopg2.connect(DB_CONNECTION_STRING)
        cursor = conn.cursor()
        
        query_embedding = query_embedding.tolist()
        
        query = sql.SQL("""
            SELECT id, document, source, (embedding <=> %s::vector) AS distance
            FROM text_embeddings_anky
            WHERE (embedding <=> %s::vector) < %s
            ORDER BY distance 
            LIMIT 15;
        """)
        cursor.execute(query, (query_embedding, query_embedding, threshold))
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error finding similar embeddings: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def make_openai_call_(combined_query, query_text):
    """Make OpenAI API call for query processing"""
    try:
        response = get_openai_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. You are a specialized assistant tasked with analyzing a set of similar documents. You are an expert assistant specialized in analyzing documents. Your task is to carefully read the provided document and extract the information that best answers the given query. If relevant information is found, include the file path in your response. If no relevant information is found, do not mention the file name or path"},
                {"role": "user", "content": f"Here are the similar documents:\n{combined_query}"},
                {"role": "user", "content": f"Based on the provided documents, here is the query: {query_text}. Provide a concise and accurate response. Also write the file path"}
            ]
        )
        
        content = response.choices[0].message.content
        return content
        
    except Exception as e:
        print(f"Error making OpenAI call: {e}")
        return 'Error in OpenAI call'

@csrf_exempt
def handle_query(request):
    """Handle query processing with similarity search"""
    try:
        data = json.loads(request.body)
        query_text = data.get('prompt')
        
        if not query_text:
            return JsonResponse({"error": "Query text is required"}, status=400)
        
        query_embedding = get_embedding(query_text, model="text-embedding-ada-002")
        if not query_embedding:
            return JsonResponse({"error": "Failed to generate query embedding"}, status=500)
        
        query_embedding = np.array(query_embedding)
        
        try:
            similar_docs = find_similar_embeddings(query_embedding)
            if similar_docs:
                # Limit to the top 10 similar documents
                top_docs = similar_docs[:10]
                print("Top docs:", top_docs)
        
                # Create a detailed combined_query including the top 10 similar documents
                combined_query = ""
                for idx, doc in enumerate(top_docs):
                    combined_query += f"Document {idx+1}: ID: {doc[0]}, Content: {doc[1]}, Source: {doc[2]}, Distance: {doc[3]}\n"
        
                # Make the OpenAI call
                print("Combined Query: ", combined_query)
                print("Query Text: ", query_text)
                openai_response = make_openai_call_(combined_query, query_text)
        
                response = {
                    "query": query_text,
                    "openai_response": openai_response
                }
                
                return JsonResponse(response, status=200)
            else:
                return JsonResponse({"error": "No similar documents found"}, status=404)
        
        except Exception as e:
            print("Error:", str(e))
            return JsonResponse({"error": str(e)}, status=500)
    
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        print("Error:", str(e))
        return JsonResponse({"error": str(e)}, status=500)
