from enum import StrEnum


class MediaType(StrEnum):
    ANIME = "anime"
    MANGA = "manga"


class LibraryStatus(StrEnum):
    WATCHING = "watching"
    READING = "reading"
    COMPLETED = "completed"
    PLANNED = "planned"
    PAUSED = "paused"
    DROPPED = "dropped"
