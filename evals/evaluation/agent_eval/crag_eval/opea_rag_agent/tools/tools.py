# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

import requests
from tools.pycragapi import CRAG


def search_knowledge_base(query: str) -> str:
    """Search a knowledge base about music and singers for a given query.

    Returns text related to the query.
    """
    url = os.environ.get("WORKER_AGENT_URL")
    print(url)
    proxies = {"http": ""}
    payload = {"messages": query, "stream": False}
    response = requests.post(url, json=payload, proxies=proxies)
    return response.json()["text"]


def search_artist_entity_by_name(artist_name: str) -> dict:
    """Search for music artists by name."""
    api = CRAG()
    return api.music_search_artist_entity_by_name(artist_name)


def search_song_entity_by_name(song_name: str) -> dict:
    """Search for songs by name."""
    api = CRAG()
    return api.music_search_song_entity_by_name(song_name)


def get_billboard_rank_date(rank: int, date: str = None) -> dict:
    """Get Billboard ranking for a specific rank and date."""
    api = CRAG()
    rank = int(rank)
    return api.music_get_billboard_rank_date(rank, date)


def get_billboard_attributes(date: str, attribute: str, song_name: str) -> dict:
    """Get attributes of a song from Billboard rankings."""
    api = CRAG()
    return api.music_get_billboard_attributes(date, attribute, song_name)


def get_grammy_best_artist_by_year(year: int) -> dict:
    """Get the Grammy Best New Artist for a specific year."""
    api = CRAG()
    year = int(year)
    return api.music_grammy_get_best_artist_by_year(year)


def get_grammy_award_count_by_artist(artist_name: str) -> dict:
    """Get the total Grammy awards won by an artist."""
    api = CRAG()
    return api.music_grammy_get_award_count_by_artist(artist_name)


def get_grammy_award_count_by_song(song_name: str) -> dict:
    """Get the total Grammy awards won by a song."""
    api = CRAG()
    return api.music_grammy_get_award_count_by_song(song_name)


def get_grammy_best_song_by_year(year: int) -> dict:
    """Get the Grammy Song of the Year for a specific year."""
    api = CRAG()
    year = int(year)
    return api.music_grammy_get_best_song_by_year(year)


def get_grammy_award_date_by_artist(artist_name: str) -> dict:
    """Get the years an artist won a Grammy award."""
    api = CRAG()
    return api.music_grammy_get_award_date_by_artist(artist_name)


def get_grammy_best_album_by_year(year: int) -> dict:
    """Get the Grammy Album of the Year for a specific year."""
    api = CRAG()
    year = int(year)
    return api.music_grammy_get_best_album_by_year(year)


def get_all_awarded_artists() -> dict:
    """Get all artists awarded the Grammy Best New Artist."""
    api = CRAG()
    return api.music_grammy_get_all_awarded_artists()


def get_artist_birth_place(artist_name: str) -> dict:
    """Get the birthplace of an artist."""
    api = CRAG()
    return api.music_get_artist_birth_place(artist_name)


def get_artist_birth_date(artist_name: str) -> dict:
    """Get the birth date of an artist."""
    api = CRAG()
    return api.music_get_artist_birth_date(artist_name)


def get_members(band_name: str) -> dict:
    """Get the member list of a band."""
    api = CRAG()
    return api.music_get_members(band_name)


def get_lifespan(artist_name: str) -> dict:
    """Get the lifespan of an artist."""
    api = CRAG()
    return api.music_get_lifespan(artist_name)


def get_song_author(song_name: str) -> dict:
    """Get the author of a song."""
    api = CRAG()
    return api.music_get_song_author(song_name)


def get_song_release_country(song_name: str) -> dict:
    """Get the release country of a song."""
    api = CRAG()
    return api.music_get_song_release_country(song_name)


def get_song_release_date(song_name: str) -> dict:
    """Get the release date of a song."""
    api = CRAG()
    return api.music_get_song_release_date(song_name)


def get_artist_all_works(artist_name: str) -> dict:
    """Get all works by an artist."""
    api = CRAG()
    return api.music_get_artist_all_works(artist_name)
