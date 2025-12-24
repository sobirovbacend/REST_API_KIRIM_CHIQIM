from django.db import models
import uuid

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True,unique=True, editable=True, default=uuid.uuid4())
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        abstract = True


