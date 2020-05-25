from api_utils import ApiUtils

import urllib.request
import json
import csv
import argparse
import sys
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

BASE_URL_ARTISTS = "https://musicbrainz.org/ws/2/artist?query=%s&limit=%i&offset=%i&fmt=json"
SPECIAL_PARAMS = ['output', 'max_songs', 'begin', 'end']


def artist_query_for_params(params):
    """
    Builds MusicBrainz query according to a given
    set of params
    """
    query = ''
    for key in params.keys():
        if key in SPECIAL_PARAMS:
            continue
        if params[key]:
            if isinstance(params[key], list):
                if len(query) == 0:
                    query += '%s:(%s)' % (key, ' OR '.join(params[key]))
                else:
                    query += ' AND %s:(%s)' % (key, ' OR '.join(params[key]))
            else:
                if len(query) == 0:
                    query += '%s:%s' % (key, params[key])
                else:
                    query += ' AND %s:%s' % (key, params[key])
    if len(query) == 0:
        query += 'begin:[%i TO %i]' % (params['begin'], params['end'])
    else:
        query += ' AND begin:[%i TO %i]' % (params['begin'], params['end'])
    return query.replace(' ', '%20')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-country', action='append')
    parser.add_argument('-gender', action='append')
    parser.add_argument('-genre',  action='append')
    parser.add_argument('-begin', type=int, default=0)
    parser.add_argument('-end', type=int, default=10000)

    parser.add_argument('-max_songs', type=int, default=1000)
    parser.add_argument('-output', type=str, default='out.csv')

    params = vars(parser.parse_args())
    params['tag'] = params['genre']
    params.pop('genre', None)

    logger.info('querying artists for following params')
    logger.info(params)

    artists_for_criteria = json.loads(urllib.request.urlopen(
        BASE_URL_ARTISTS % (
            artist_query_for_params(params),
            100,
            0
        )).read())

    parsed_artists = []
    finished = False
    api = ApiUtils(params, logger)
    logger.info("parsing data from %i artists" % artists_for_criteria['count'])
    with open(params['output'], 'a', newline='') as csvfile:
        fieldnames = ['title', 'artist', 'beat_count', 'bpm', 'key',
                      'key_scale', 'average_loudness', 'length', 'energy',
                      'speechiness', 'acousticness', 'instrumentalness',
                      'liveness', 'danceability', 'loudness', 'valence',
                      'time_signature', 'timbre', 'tonal_atonal',
                      'voice_instrumental', 'mood_sad', 'mood_relaxed',
                      'mood_party', 'mood_happy', 'mood_electronic',
                      'mood_aggressive', 'mood_acoustic']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(int((artists_for_criteria['count']) // 100) + 1):
            logger.info(BASE_URL_ARTISTS % (
                artist_query_for_params(params),
                100,
                100 * i
            ))
            artists_for_criteria = json.loads(
                urllib.request.urlopen(BASE_URL_ARTISTS % (
                    artist_query_for_params(params),
                    100,
                    100 * i
                )).read())
            for artist in artists_for_criteria['artists']:
                if not artist['name'] in parsed_artists:
                    try:
                        if not api.parse_entries_for_artist(artist, writer):
                            finished = True
                            break
                    except Exception as e:
                        logger.error("%s failed: %s" % (artist['name'], e))
                    parsed_artists.append(artist['name'])
            if finished:
                break
