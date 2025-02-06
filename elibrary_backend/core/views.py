from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
import fitz  # PyMuPDF
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
import os
from .models import Book
from .serializers import BookSerializer
from langchain.chat_models import ChatOpenAI


# Load FAISS index safely
faiss_index_path = "faiss_index"
faiss_index = None  # Default to None

if os.path.exists(faiss_index_path):
    faiss_index = FAISS.load_local(faiss_index_path)

# Extract text from PDF
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    return " ".join(page.get_text() for page in doc)

# Index books in FAISS
def index_books():
    books = Book.objects.all()
    texts = [extract_text_from_pdf(book.pdf_file.path) for book in books]
    
    documents = [Document(page_content=text) for text in texts]
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    text_chunks = text_splitter.split_documents(documents)
    
    embeddings = OpenAIEmbeddings()
    index = FAISS.from_documents(text_chunks, embeddings)
    index.save_local(faiss_index_path)
    
    return index

# Initialize FAISS index if missing
if not faiss_index:
    faiss_index = index_books()

@api_view(['POST'])
def chatbot(request):
    query = request.data.get('query')
    if not query:
        return Response({"error": "Query is required"}, status=400)
    
    # Retrieve relevant documents
    result = faiss_index.similarity_search(query, k=1)

    if not result:
        return Response({"answer": "No relevant information found."})

    chat_model = ChatOpenAI(temperature=0)
    prompt = f"Answer the question based on the following context: {result[0].page_content}"
    chat = chat_model.generate([prompt])

    return Response({"answer": chat['text']})

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]  

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def download(self, request, pk=None):
        book = self.get_object()
        return Response({'file_url': book.pdf_file.url})

class ChatbotView(APIView):
    def post(self, request):
        query = request.data.get('query', '')
        answer = f"This is a placeholder answer. You asked: {query}"
        return Response({'answer': answer})

@api_view(['GET'])
def search_books(request):
    query = request.GET.get('query')
    if query:
        search_vector = SearchVector('title', 'author')
        search_query = SearchQuery(query)
        books = Book.objects.annotate(
            rank=SearchRank(search_vector, search_query)
        ).filter(rank__isnull=False).order_by('-rank')
        results = [{'title': book.title, 'author': book.author} for book in books]
        return Response({'results': results})
    return Response({'results': []})
