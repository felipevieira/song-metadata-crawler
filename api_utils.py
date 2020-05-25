import json
import urllib
import requests
import configparser

# MusicBrazins & AcousticBrainz API
BASE_URL_ARTISTS = "https://musicbrainz.org/ws/2/artist?query=%s&limit=%i&offset=%i&fmt=json"
BASE_URL_RECORDING = "http://musicbrainz.org/ws/2/recording?query=%s&limit=%i&offset=%i&fmt=json"
BASE_ACOUSTIC_BRAINZ_HL = 'https://acousticbrainz.org/api/v1/high-level?recording_ids=%s'
BASE_ACOUSTIC_BRAINZ_LL = 'https://acousticbrainz.org/api/v1/low-level?recording_ids=%s'
# Spotify API
BASE_SPOTIFY = 'https://api.spotify.com/v1/search?q=%s&type=track'
BASE_AUDIO_FEATURES_SPOTIFY = 'https://api.spotify.com/v1/audio-features/%s'
BASE_SPOTIFY_TOKEN = 'https://accounts.spotify.com/api/token'

config = configparser.ConfigParser()
config.read('config.conf')
CLIENT_ID = config.get('DEFAULT', 'SPOTIFY_CLIENT_ID')
CLIENT_SECRET = config.get('DEFAULT', 'SPOTIFY_CLIENT_SECRET')
SONGS_PER_ARTIST = int(config.get('DEFAULT', 'SONGS_PER_ARTIST'))

PARSED_SONGS = []


class ApiUtils:
    def __init__(self, params, logger):
        self.params = params
        self.logger = logger
        self.spotify_token = None
        self.parsed_songs = 0

    def recording_query_for_params(self, arid):
        query = 'arid:%s' % arid
        if 'date' in self.params.keys():
            query += ' AND date:[%s TO %s]' % (
                self.params['date'][0], self.params['date'][1])
        return query.replace(' ', '%20')

    def get_spotify_data(self, track, artist):
        try:
            req = urllib.request.Request(BASE_SPOTIFY % urllib.parse.quote((
                '%s %s' % (track, artist))))
            req.add_header('Authorization', 'Bearer ' + (
                self.spotify_token or ''))
            req.add_header('Accept-Charset', 'utf-8')
            req_open = urllib.request.urlopen(req)
            content = json.loads(req_open.read())
        # Renew (or generate) access token
        except Exception as e:
            code_payload = {
                "grant_type": "client_credentials",
            }
            response_data = json.loads(
                requests.post(BASE_SPOTIFY_TOKEN, data=code_payload,
                              auth=(CLIENT_ID, CLIENT_SECRET)).text)
            self.spotify_token = response_data['access_token']
            return

        if len(content['tracks']['items']) > 0:
            spotify_id = content['tracks']['items'][0]['id']
            req = urllib.request.Request(
                BASE_AUDIO_FEATURES_SPOTIFY % spotify_id)
            req.add_header('Authorization', 'Bearer ' + self.spotify_token)
            return json.loads(urllib.request.urlopen(req).read())

    def parse_entry(self, metadata, acoustic_info_ll, acoustic_info_hl):
        try:
            spotify_audio_features = self.get_spotify_data(
                metadata['title'], metadata['artist-credit'][0]['name'])

            if not spotify_audio_features:
                return

            binary_classifiers = ['timbre', 'tonal_atonal',
                                  'voice_instrumental', 'mood_sad',
                                  'mood_relaxed', 'mood_party',
                                  'mood_happy', 'mood_electronic',
                                  'mood_aggressive', 'mood_acoustic']
            parsed_entry = {}
            # parsed_entry.append(acoustic_info_ll[metadata['id']]['0']['metadata']['tags']['musicbrainz_recordingid'][0])
            parsed_entry['title'] = metadata['title']
            parsed_entry['artist'] = " | ".join(
                [artist['name'] for artist in metadata['artist-credit']])
            parsed_entry['beat_count'] = acoustic_info_ll[metadata['id']]['0'][
                'rhythm']['beats_count']
            parsed_entry['bpm'] = \
                acoustic_info_ll[metadata['id']]['0']['rhythm']['bpm']
            parsed_entry['key'] = acoustic_info_ll[metadata['id']]['0'][
                'tonal']['key_key']
            parsed_entry['key_scale'] = \
                acoustic_info_ll[metadata['id']]['0']['tonal']['key_scale']
            parsed_entry['average_loudness'] = \
                acoustic_info_ll[metadata['id']]['0']['lowlevel'][
                    'average_loudness']
            parsed_entry['length'] = \
                acoustic_info_ll[metadata['id']]['0']['metadata'][
                    'audio_properties']['length']
            parsed_entry['energy'] = spotify_audio_features['energy']
            parsed_entry['speechiness'] = spotify_audio_features['speechiness']
            parsed_entry['acousticness'] = \
                spotify_audio_features['acousticness']
            parsed_entry['instrumentalness'] = \
                spotify_audio_features['instrumentalness']
            parsed_entry['liveness'] = spotify_audio_features['liveness']
            parsed_entry['danceability'] = \
                spotify_audio_features['danceability']
            parsed_entry['loudness'] = spotify_audio_features['loudness']
            parsed_entry['valence'] = spotify_audio_features['valence']
            parsed_entry['time_signature'] = spotify_audio_features['loudness']
            for binary_classifier in binary_classifiers:
                parsed_entry[binary_classifier] = \
                    acoustic_info_hl[metadata['id']]['0']['highlevel'][
                        binary_classifier]['value']
            return parsed_entry
        except Exception as e:
            return None

    def parse_entries_for_artist(self, metadata, csv_writer):
        PARSED_SONGS_ARTIST = []
        self.logger.info("parsing songs for %s" % metadata['name'])
        songs = 0
        recordings_for_criteria = json.loads(
            urllib.request.urlopen(BASE_URL_RECORDING % (
                self.recording_query_for_params(metadata['id']),
                100,
                0
            )).read())

        for i in range((int(recordings_for_criteria['count']) // 100) + 1):
            recordings_for_criteria = json.loads(
                urllib.request.urlopen(BASE_URL_RECORDING % (
                    self.recording_query_for_params(metadata['id']),
                    100,
                    i
                )).read())
            for recording in recordings_for_criteria['recordings']:
                if not recording['id'] in PARSED_SONGS and \
                   not recording['title'] in PARSED_SONGS_ARTIST:
                    PARSED_SONGS.append(recording['id'])
                    PARSED_SONGS_ARTIST.append(recording['title'])
                    acoustic_info_ll = json.loads(urllib.request.urlopen(
                        BASE_ACOUSTIC_BRAINZ_LL % (
                            recording['id']
                        )).read())
                    acoustic_info_hl = json.loads(urllib.request.urlopen(
                        BASE_ACOUSTIC_BRAINZ_HL % (
                            recording['id']
                        )).read())
                    if (len(acoustic_info_ll) > 1):
                        try:
                            parsed_entry = self.parse_entry(
                                recording, acoustic_info_ll, acoustic_info_hl)
                            if parsed_entry:
                                self.parsed_songs += 1
                                songs += 1
                                self.logger.info(
                                    "parsed %i/%i songs (%.1f%%)" % (
                                        self.parsed_songs,
                                        self.params['max_songs'],
                                        100*(self.parsed_songs
                                             / self.params['max_songs'])))
                                csv_writer.writerow(parsed_entry)
                                if self.parsed_songs == self.params['max_songs']:
                                    return False
                                if songs >= SONGS_PER_ARTIST:
                                    return True
                        except Exception as e:
                            continue
        return True
