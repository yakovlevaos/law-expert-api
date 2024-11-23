from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Mode(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Competencies(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Duration(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Platform(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Game(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, null=True, blank=True)
    title = models.TextField(unique=True)
    description = models.TextField(null=True, blank=True)
    cover_image = models.ImageField(upload_to="games/")
    duration = models.CharField(max_length=255)
    duration_type = models.ForeignKey(Duration, on_delete=models.CASCADE)
    genres = models.ManyToManyField(Genre)
    competencies = models.ManyToManyField(Competencies)
    platforms = models.ManyToManyField(Platform)
    modes = models.ManyToManyField(Mode)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Игра"
        verbose_name_plural = "Игры"


class ScreenShot(models.Model):
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="screen_shots"
    )
    screen_shot = models.ImageField(upload_to="games/")