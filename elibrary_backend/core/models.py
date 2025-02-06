from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.search import SearchVectorField
from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    pdf_file = models.FileField(upload_to='books/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    search_vector = SearchVectorField()

    def __str__(self):
        return self.title

    
class CustomUser(AbstractUser):
    pass
