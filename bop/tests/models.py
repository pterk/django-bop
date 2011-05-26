from django.db import models

# Test 'model'
class Thing(models.Model):
    label = models.CharField(max_length=255, unique=True) 
    
    class Meta:
        app_label = 'bop'
        permissions = (
            ('do_thing', 'User can do their thing'),
            ('mark_thing', 'User can mark  their thing'),
            )

    def __unicode__(self):
        return self.label
