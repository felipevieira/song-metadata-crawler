# Song Metadata Crawler

Song Metadata Crawler (SMC) is a a tool that leverages public APIs from [MusicBrainz](https://musicbrainz.org), [AcousticBrainz](https://acousticbrainz.org/) and [Spotify](https://www.spotify.com) to fetch high-level and low-level song metadata.

## Requirements
- Python 3.6+  
... and that's it! :rocket:

## Usage Instructions
### Install required depedencies
`pip install -r requirements.txt`
### Fill in configurations file
SMC requires credentials of a valid Spotify app in order to fetch data. You can create your own app in https://developer.spotify.com/dashboard/applications.   
Once you're done just copy the contents of `config.conf.example` to your own `config.conf` and put your `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` into this file.

### Run the crawler
Crawler can be executed using the main `crawler.py` entrypoint:  
`python crawler.py [OPTIONS]`  
  
... and wait! :hourglass_flowing_sand: Crawling will take some time to fetch data that match your filters. In the meantime you will be prompted about the progress.

#### Supported options
| Option      | Semantics                                                                       | Default                           | Example                                               |
|-------------|---------------------------------------------------------------------------------|-----------------------------------|-------------------------------------------------------|
| -country    | 2-letter code (ISO 3166-1 alpha-2) for the artist's main associated country <br> (list of codes can be found [here](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes))   | None (won't filter by country)    | `python crawler.py -country US -country BR`           |
| -gender     | Artist gender                                                                   | All (female, male, unknown)       | `python crawler.py -gender female`                      |
| -genre      | Artist music Genre                                                              | None (won't filter by genre)      | `python crawler.py -genre pop -genre rock -genre metal` |
| -begin      | Represents the date when the group <br>first formed or person was born          | None (won't filter by begin date) | `python crawler.py -begin 1990`                         |
| -end        | Represents the date when the group <br>last dissolved or person died            | None (won't filter by end date)   | `python crawler.py -end 2000`                           |
| --max-songs | Maximum number of songs to be crawled                                           | 5000                              | `python crawler.py --max-songs 10000`                   |
| -output     | Output filename                                                                 | out.csv                           | `python crawler.py -output myfile.csv`                  |
