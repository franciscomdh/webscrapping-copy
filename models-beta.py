# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class IhCiudad(models.Model):
    idciudad = models.AutoField(primary_key=True)
    idregion = models.IntegerField()
    idprovincia = models.IntegerField()
    nombre = models.CharField(max_length=200)
    citycode = models.CharField(max_length=3, blank=True, null=True)
    idpais = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ih_ciudad'


class IhPais(models.Model):
    idpais = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    countrycode = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ih_pais'


class IhVenues(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombrepais = models.CharField(max_length=30, blank=True, null=True)
    nombreciudad = models.CharField(max_length=450, blank=True, null=True)
    venue = models.CharField(max_length=600, blank=True, null=True)
    latitud = models.CharField(max_length=60, blank=True, null=True)
    longitud = models.CharField(max_length=60, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ih_venues'
