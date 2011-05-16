from django.db import models

# Test 'model'
class Thing(models.Model):
    label = models.CharField(max_length=255, unique=True) 
    
    class Meta:
        app_label = 'bop'

