import os
from azure.search.documents import SearchClient 
from azure.search.documents.models import VectorizedQuery   
from azure.core.credentials import AzureKeyCredential
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class SearchCustomer:
    
    def __init__(self):
        # assign the Search variables for Azure Cogintive Search - use .env file and in the web app configure the application settings
        AZURE_SEARCH_ENDPOINT = os.environ.get("AZURE_SEARCH_ENDPOINT")
        AZURE_SEARCH_ADMIN_KEY = os.environ.get("AZURE_SEARCH_ADMIN_KEY")
        AZURE_SEARCH_INDEX = os.environ.get("AZURE_SEARCH_INDEX_CUSTOMER")
        credential_search = AzureKeyCredential(AZURE_SEARCH_ADMIN_KEY)
        OPENAI_EMBED_MODEL = os.environ.get("OPENAI_EMBED_MODEL")

        self.sc = SearchClient(endpoint=AZURE_SEARCH_ENDPOINT, index_name=AZURE_SEARCH_INDEX, credential=credential_search)
        self.model = OPENAI_EMBED_MODEL
        self.openai_client = OpenAI()

        print(f"init search with index: {AZURE_SEARCH_INDEX}")
    
    def get_embedding(self, text, model):
        text = text.replace("\n", " ")
        return self.openai_client.embeddings.create(input = [text], model=model).data[0].embedding
    
    def search_hybrid(self, query: str) -> str:
        vector_query = VectorizedQuery(vector=self.get_embedding(query, self.model), k_nearest_neighbors=5, fields="contentVector")
        results = []
        print(f"in search_customer querying: {query}")
        try:
            r = self.sc.search(  
                search_text=query,  # set this to engage a Hybrid Search
                vector_queries= [vector_query],  
                select=["category", "sourcefile", "content"],
                top=3,
            )  
            for doc in r:
                    results.append(f"[CATEGORY:  {doc['category']}]" + " " + f"[SOURCEFILE:  {doc['sourcefile']}]" + doc['content'])
                    #print("\n".join(f"[CATEGORY:  {doc['category']}]"  + " " + f"[SOURCEFILE:  {doc['sourcefile']}]"))
        except Exception as yikes:
                    print(f'\n\nError in SearchClient: "{yikes}"')

        #print("\n".join(results))
        return ("\n".join(results))