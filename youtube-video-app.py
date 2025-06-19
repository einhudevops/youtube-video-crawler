from googleapiclient.discovery import build
import pandas as pd
import time
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import VARCHAR, Boolean, Column, DateTime, ForeignKey, Integer
from sqlalchemy import update
from sqlalchemy import func, delete
from sqlalchemy.orm import relationship
import isodate
from time import sleep
from datetime import datetime, timedelta
Base = declarative_base()

class Yt(Base):
    __tablename__ = 'youtube_channel'
    id = Column(Integer, primary_key=True)
    channel_id = Column("channel_id", VARCHAR(32))
    channel_name = Column("channel_name", VARCHAR(32))
    playlist_id= Column("playlist_id", VARCHAR(32))
    active= Column("active", VARCHAR(32))
    last_time_finished = Column("last_time_finished", DateTime)
    youtube_st = relationship("Yt_st", back_populates="youtube_ch")
    youtube_vdo = relationship("Yt_vd", back_populates="youtube_vdo")

class Yt_st(Base):
    __tablename__ = 'youtube_st'
    id = Column(Integer, primary_key=True)
    subscribers= Column("subscribers", Integer)
    views= Column("views", Integer)
    videos= Column("videos", Integer)
    date= Column('date', DateTime)
    youtube_channel_id = Column(Integer, ForeignKey('youtube_channel.id'))
    youtube_ch = relationship("Yt", back_populates="youtube_st")

class Yt_vd(Base):
    __tablename__ = 'youtube_vd'
    id = Column(Integer, primary_key=True)
    video_id = Column("video_id",  VARCHAR(32))
    youtube_channel_id = Column(Integer, ForeignKey('youtube_channel.id'))
    youtube_vdo = relationship("Yt", back_populates="youtube_vdo")
    nlp_id = Column(Integer, ForeignKey('nlp.id'), nullable=True)
    text =Column("text",  VARCHAR(1024))
    description = Column("description",  VARCHAR(16348))
    tags = Column("tags",  VARCHAR(1024))
    date = Column('date', DateTime)
    views = Column("views", Integer)
    likes = Column("likes", Integer)
    comments = Column("comments", Integer)
    definition = Column("definition",  VARCHAR(32))
    caption = Column("caption",  VARCHAR(32))
    durationsecs = Column("durationsecs", Integer)
    tagcount = Column("tagcount", Integer)

class NLP(Base):
    __tablename__ = 'nlp'
    id = Column('id', Integer, primary_key=True)
    Category = Column('category', VARCHAR(255))

class All_content(Base):
    __tablename__ = 'all_content'
    id = Column(Integer, primary_key=True)
    content_id = Column("content_id", Integer)
    network_id = Column("network_id", Integer)
    nlp_id = Column('nlp_id', Integer)
    ht_check = Column('ht_check', VARCHAR(32))
    keyword_check = Column('keyword_check', VARCHAR(32))

class Yt_api(Base):
    __tablename__ = 'youtube_api_key'
    id = Column(Integer, primary_key=True)
    gmail = Column('gmail', VARCHAR(32))
    api_key = Column('api_key', VARCHAR(64))
    active = Column('active', VARCHAR(32))
    last_time = Column('last_time', DateTime)
    
engine = create_engine('postgresql://fbs:yah7WUy1Oi8G@192.168.11.202:5432/fbs', echo=False)
#Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

min_time = session.query(func.min(Yt_api.last_time)).filter(Yt_api.active == 'true').first() # min_time
# insert your vd_crawler
re_api_key = session.query(Yt_api.api_key, Yt_api.gmail).filter(Yt_api.last_time == min_time[0]).first()
print("API Mail : " + re_api_key[1])
api_key = re_api_key[0]
youtube = build('youtube', 'v3', developerKey= api_key)
start_time = time.time()

craw_channel =session.query(Yt.playlist_id,Yt.id,Yt.channel_name).filter(Yt.active == 'true').order_by(Yt.last_time_finished).all()
for i in craw_channel:
    playlist_id = i.playlist_id
    playlist_id = f"{playlist_id}"
    Id = i.id
    channelname = i.channel_name
    print("Channel ID : "+ str(Id))
    print("Playlist ID : " + playlist_id)
    print("Channel Name :  \033[0m" + f"\033[31m{channelname}\033[0m")

    date_obj = datetime.now()
    print(date_obj)
    stmt2 = (update(Yt).where(Yt.id == Id).values(last_time_finished = date_obj))
    session.execute(stmt2, execution_options={"synchronize_session": False})
    session.commit() 
    

    def get_video_ids(youtube, Playlist_id):
        video_ids = []
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId= str(Playlist_id),
            maxResults = 50
        )
        response = request.execute()
        
        for item in response['items']:
            video_ids.append(item['contentDetails']['videoId'])
            
        next_page_token = response.get('nextPageToken')
        while next_page_token is not None:
            request = youtube.playlistItems().list(
                        part='contentDetails',
                        playlistId = str(Playlist_id),
                        maxResults = 50,
                        pageToken = next_page_token)
            response = request.execute()

            for item in response['items']:
                video_ids.append(item['contentDetails']['videoId'])

            next_page_token = response.get('nextPageToken')
        return video_ids
    try:
        video_ids = get_video_ids(youtube, playlist_id)  # get video ids
        print("Total Videos : " + str(len(video_ids)))

        if len(video_ids)>100:
            video_ids=video_ids[0:100]
        elif len(video_ids)<100:
            video_ids=video_ids

        print("Crwal Videos : " + str(len(video_ids)))

        def get_video_details(youtube, video_ids):
            all_video_info = []
            for i in range(0, len(video_ids), 50):
                request = youtube.videos().list(
                    part="snippet,contentDetails,statistics",
                    id=','.join(video_ids[i:i+50])
                )
                response = request.execute() 

                for video in response['items']:
                    stats_to_keep = {'snippet': ['channelTitle', 'title', 'description', 'tags', 'publishedAt'],
                                    'statistics': ['viewCount', 'likeCount', 'favouriteCount', 'commentCount'],
                                    'contentDetails': ['duration', 'definition', 'caption']
                                    }
                    video_info = {}
                    video_info['video_id'] = video['id']
                
                    for k in stats_to_keep.keys():
                        for v in stats_to_keep[k]:
                            try:
                                video_info[v] = video[k][v]
                            except:
                                video_info[v] = None

                    all_video_info.append(video_info)  
            return pd.DataFrame(all_video_info)

        video_df = get_video_details(youtube, video_ids) # # get video details

        # Publish datetime format change
        # video_df['publishedAt'] = pd.to_datetime(video_df['publishedAt'], format='%Y-%m-%d %H:%M:%S')
        # video_df['publishedAt'] = video_df['publishedAt'].dt.tz_convert('Asia/Yangon')
        # video_df['publishedAt'] = video_df['publishedAt'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))
        # video_df['publishedAt'] = video_df['publishedAt'].apply(lambda x: parser.parse(x)) 
        # video_df['publishedAt'] = video_df['publishedAt'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))
        # Convert 'publishedAt' to datetime and handle timezone
        
        video_df['publishedAt'] = pd.to_datetime(video_df['publishedAt'], utc=True)
        # Convert to the desired timezone
        video_df['publishedAt'] = video_df['publishedAt'].dt.tz_convert('Asia/Yangon')
        # Format datetime to string in the desired format
        video_df['publishedAt'] = video_df['publishedAt'].dt.strftime('%Y-%m-%d %H:%M:%S')

        # convert duration to seconds
        video_df['durationSecs'] = video_df['duration'].apply(lambda x: isodate.parse_duration(x))
        video_df['durationSecs'] = video_df['durationSecs'].astype('timedelta64[s]')
        video_df['durationSecs'] = video_df['durationSecs'].astype(int)
        video_df['durationSecs'] = video_df['durationSecs'].astype(str)

        # Add tag count
        video_df['tagCount'] = video_df['tags'].apply(lambda x: 0 if x is None else len(x))
        video_df['tagCount'] = video_df['tagCount'].astype(str)
        count = 0
        count1 = 0
        # Add to db
        for i in range(len(video_df)):
            Video_id = video_df['video_id'].iloc[i]
            Title=video_df['title'].iloc[i]
            Description=video_df['description'].iloc[i]
            Tags= video_df['tags'].iloc[i]
            PublishedAt = video_df['publishedAt'].iloc[i]
            ViewCount= video_df['viewCount'].iloc[i]
            LikeCount= video_df['likeCount'].iloc[i]
            CommentCount = video_df['commentCount'].iloc[i]
            Definition = video_df['definition'].iloc[i]
            Caption = video_df['caption'].iloc[i]
            DurationSecs = video_df['durationSecs'].iloc[i]
            TagCount = video_df['tagCount'].iloc[i]
            same_id =session.query(Yt_vd.video_id).filter(Yt_vd.video_id == Video_id).first()
            #print(same_id[0])
            if same_id:
                stmt = (update(Yt_vd).where(Yt_vd.video_id == same_id[0]).values(views=ViewCount, likes=LikeCount,comments=CommentCount)) # update views, like, comment
                session.execute(stmt, execution_options={"synchronize_session": False})
                session.commit() 
                count += 1
                #session.rollback()
            else:
                add_vd= Yt_vd(video_id=Video_id, text=Title, description=Description, tags=Tags, date=PublishedAt, youtube_channel_id=Id, views=ViewCount, 
                        likes=LikeCount, comments=CommentCount, definition=Definition, caption=Caption, durationsecs=DurationSecs, tagcount=TagCount) # add youtube_vd 
                session.add(add_vd)
                session.commit() 
                #session.rollback()
                count1 += 1
                latest_id =session.query(func.max(Yt_vd.id)).first() # add id to all_content
                add_id = All_content(content_id = latest_id[0], network_id =2)
                session.add(add_id)
                session.commit() 
                # session.rollback()
        print("Updated video : " + str(count))
        print("Added video : " + str(count1))
        print("\033[32mSucessfully Added to DB \033[0m")
        print("--------------------------------")    
    except Exception as e:
        print(e)

date_format = "%Y-%m-%d %H:%M:%S"
date_obj = datetime.now()
stmt1 = (update(Yt_api).where(Yt_api.gmail == re_api_key[1]).values(last_time = date_obj)) # update views, like, comment
session.execute(stmt1, execution_options={"synchronize_session": False})
session.commit() 
session.rollback()
