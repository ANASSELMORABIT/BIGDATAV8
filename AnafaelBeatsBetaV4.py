from flask import Flask, redirect, url_for, request, render_template, jsonify
from youtube_search import YoutubeSearch
import os
import requests
import mysql.connector
import random
import pandas as pd
import datetime



#---------------------------Listas de API KEYS -------------------------------------------

Recomended_Songs=["c63b548607msh41199f8ec262e82p1ce9c3jsn40b26505dd96","02f07b9576mshffa54c2618cbb67p13148cjsnc4b7b5ddb9a2","863788d9aemsh21538477c437526p13e476jsna4c13406aea3","e075800041msh15289393b73dd14p109603jsn90cd0d0424b8"]
Recomended_ARTIST=["b09b570d46msh9ec231073ed2b69p1712aejsna283de1d0ccd","29880ca0fbmsh566e113215704c7p110c55jsn02062b11680b","d8e04f7929msh53e2e72d154bf06p1a716ejsne3908c018d30","e9773a1515msh6c65812cc3ce83ap11e46djsn4dd6284ac7c5"]
Recomended_ALBUM=["4c13866740msh27adf353370af5ep1ab6c5jsn7688b8bb227d","abfc26b3bcmsh9582e79ea4277b8p17834bjsn19de9a9355d8","3d7da4c793msh13e60ea3130926ap1fb16cjsnd51dabd3c916"]
Search_songs=["1fc72ce470msh8df5aedb83df66bp1aacc9jsn19b4618a2c66","7be32ffc1bmsh224552f2bca1867p10230cjsnb52f12c89d44","43b2ee84camshecec3792888a607p1a114bjsn13c7ffcb0784"]
downloadVideo=["e166101c8bmsh05b406f6a14c124p1d87ccjsn263c82c76a8c","bf178997d9msh3f2acaf10cc3ca2p12af11jsn437036e2f58c","1b4594e61emsh6cf0b78c567ba7dp11524cjsn6bf8fd148e4c"]




#?----------------------- Preguntas Random -----------------------------------------------
#Estos preguntas nos ayuda a recuperar la contraseña de las cuentas de los usuarios cuando quieren cambiar la conraseña o 

Questions=["What is your favorite color?",\
           "What is your favorite animal?",\
            "What is your favorite food?",\
            "What is your favorite movie?",\
            "What is your favorite book?",\
            "What is your favorite game?",\
            "What is your favorite sport?",\
            "What is your favorite TV show?",\
            "What is your favorite music?",\
            "What is your favorite song?"]

#?---------------------Funciones de base de datos---------------------------------------

def CreatDataBase():
    connexion = mysql.connector.connect(host="localhost", user="root", passwd="")
    cursor=connexion.cursor()
    query="CREATE DATABASE IF NOT EXISTS `Users`;"
    cursor.execute(query)
    connexion.commit()
    connexion.close()
    return True

CreatDataBase()

def ConsultarUser(Username,Password):
    global user_id
    
    connexion = mysql.connector.connect(host="localhost", user="root", passwd="", database="Users")
    cursor=connexion.cursor()
    query="SELECT * FROM `UserData` WHERE `username`=%s AND `password`=%s;"
    cursor.execute(query, (Username, Password))
    result=cursor.fetchall()
    
    
    print("Resultados de la consulta:", result)
    # aqui se guarda el user_id si se encuentra en los resultados
    if result:
        user_id = result[0][0]
        
    connexion.close()
    return result

def ConsultarEmail(Username,Email):
    connexion = mysql.connector.connect(host="localhost", user="root", passwd="", database="Users")
    cursor=connexion.cursor()
    query="SELECT * FROM `UserData` WHERE `username`=%s AND `email`=%s;"
    cursor.execute(query, (Username, Email))
    result=cursor.fetchall()
    connexion.close()
    return result

def CreateTable():
    connexion = mysql.connector.connect(host="localhost", user="root", passwd="", database="Users")
    cursor=connexion.cursor()
    query="""CREATE TABLE IF NOT EXISTS `UserData` \
            (`id` int(11) NOT NULL AUTO_INCREMENT,\
            `name` varchar(255) NOT NULL, \
            `Lastname` varchar(255) NOT NULL,\
            `age` int(11) NOT NULL CHECK (`age` >= 18),\
            `password` varchar(255) NOT NULL,\
            `email` varchar(255) NOT NULL CHECK (`email` LIKE '%@%.%'),\
            `Datereg` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,\
            `Username` varchar(255) NOT NULL,\
            `Gender` varchar(255) NOT NULL CHECK (`Gender` = 'Male' OR `Gender` = 'Female'),\
            `Question` varchar(255) NOT NULL ,\
            `Answer` varchar(255) NOT NULL,\
            `profile_image_url` varchar(255) NOT NULL,\
            PRIMARY KEY (`id`)) ;"""
    cursor.execute(query)
    connexion.commit()
    connexion.close()
    return True

CreateTable()

def create_playlist_table():
    connection = mysql.connector.connect(host="localhost", user="root", passwd="", database="Users")
    cursor = connection.cursor()
    query = """CREATE TABLE IF NOT EXISTS `playlists` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `user_id` INT,
                `artist_name` VARCHAR(255),
                `album_cover` VARCHAR(255),
                `song_name` VARCHAR(255),
                `duration_minutos` DECIMAL(5,2) NOT NULL,
                `audio_url` TEXT,
                FOREIGN KEY (`user_id`) REFERENCES `UserData`(`id`)
            );"""
    cursor.execute(query)
    connection.commit()
    connection.close()

create_playlist_table()


def get_user_playlists(user_id):
    connection = mysql.connector.connect(host="localhost", user="root", passwd="", database="Users")
    cursor = connection.cursor()
    query = "SELECT * FROM `playlists` WHERE `user_id` = %s;"
    cursor.execute(query, (user_id,))
    playlists = cursor.fetchall()
    connection.close()
    return playlists

#?--------------------------Mis Funciones---------------------------------------------------

app = Flask(__name__, static_url_path='/static')

audio_file = None
audio_url = None
song_name = None
album_cover = None
artist_name = None
UserProfile = "Anafael Beats"
ProfilePicture = None
GuessQuestionGame=""
audio_urlbd = None
duration_milisegundos = None
duration_minutos = None
selected_audio_url=""

def get_top_artists(time_period):
    url = "https://genius-song-lyrics1.p.rapidapi.com/chart/artists/"
    querystring = {"time_period": time_period, "per_page": "8", "page": "1"}
    headers = {
        "X-RapidAPI-Key": "3137250defmshdfac8b9cd4ac75fp198b09jsn280dd3ced931",
        "X-RapidAPI-Host": "genius-song-lyrics1.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    
    if response.ok:
        json_data = response.json()
        if json_data and 'chart_items' in json_data:
            artists = []
            count = 0
            for item in json_data['chart_items']:
                if count >= 8:
                    break
                artist_name = item['item']['name']
                if 'Genius' in artist_name:
                    continue
                artist_image = item['item']['image_url']
                artists.append({'artist': artist_name, 'image': artist_image})
                count += 1
            print(artists)    
            return artists
    else:
        print("Error en la solicitud a la API Genius. Código de estado:", response.status_code)
        return []


def get_recommended_albums(time_period):
    
    url = "https://genius-song-lyrics1.p.rapidapi.com/chart/albums/"
    querystring = {"time_period": time_period, "per_page": "5", "page": "1"}
    headers = {
        "X-RapidAPI-Key": "9fea1c33a9msh7319205eda0130fp18e683jsnded44e0364d9",
        "X-RapidAPI-Host": "genius-song-lyrics1.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    
    
    if response.status_code == 200:
        
        json_data = response.json()
        
        
        albums = []
        for item in json_data['chart_items'][:5]:
            album_data = {
                'cover_art_thumbnail_url': item['item']['cover_art_thumbnail_url'],
                'name': item['item']['name'],
                'artist': item['item']['artist']['name']
            }
            albums.append(album_data)
        
        return albums
    else:
        print("error api albums")
        return None

def get_recommended_songs(time_period):
    url = "https://genius-song-lyrics1.p.rapidapi.com/chart/songs/"
    querystring = {"time_period": time_period, "per_page": "9", "page": "1"}
    headers = {
        "X-RapidAPI-Key": "a132f113fbmshc367ffd9c9aa416p189b05jsnd4428693ef76",
        "X-RapidAPI-Host": "genius-song-lyrics1.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        json_data = response.json()

        songs = []
        for item in json_data['chart_items'][:9]:
            song_data = {
                'artist_names': item['item']['artist_names'],
                'title': item['item']['title'],
                'song_art_image_url': item['item']['song_art_image_url']
            }
            songs.append(song_data)

        return songs
    else:
        print("Error al obtener las canciones recomendadas:", response.status_code)
        return None


@app.route('/update_search_value', methods=['POST'])
def update_search_value():
    global audio_file, audio_url, song_name, album_cover, artist_name, user_id, audio_urlbd, duration_milisegundos, duration_minutos
    required_value = request.form.get('search_value')


    url = "https://spotify23.p.rapidapi.com/search/"
    querystring = {"q": required_value, "type": "tracks", "offset": "0", "limit": "10", "numberOfTopResults": "5"}
    headers = {
        "X-RapidAPI-Key": "b778861137msha9552ee7cb9a78cp1e8314jsn7d6bee4df576",
        "X-RapidAPI-Host": "spotify23.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    
    if response.ok:
        json_data = response.json()
        if json_data and 'tracks' in json_data and 'items' in json_data['tracks'] and json_data['tracks']['items']:
            
            artist_name = json_data['tracks']['items'][0]['data']['artists']['items'][0]['profile']['name']
            album_cover = json_data['tracks']['items'][0]['data']['albumOfTrack']['coverArt']['sources'][0]['url']
            song_name = json_data['tracks']['items'][0]['data']['name']
            duration_milisegundos = json_data['tracks']['items'][0]['data']['duration']['totalMilliseconds']
            
            def milisegundos_a_minutos(duration_milisegundos):
                
                minutos = duration_milisegundos / (1000 * 60)
                return minutos
            
            duration_minutos = milisegundos_a_minutos(duration_milisegundos)
            
            

            
            
            audio_file = search_song_on_youtube(song_name)
            if audio_file:
                audio_url = f"/static/audio/{os.path.basename(audio_file)}"
            
                
    return redirect(url_for('welcome'))



def search_song_on_youtube(song_name):
    try:
        results = YoutubeSearch(song_name, max_results=1).to_dict()
        if results:
            youtube_link = f"https://www.youtube.com{results[0]['url_suffix']}"

            if youtube_link:
                audio_file = download_video(youtube_link)
                return audio_file
    except Exception as e:
        print("Error searching for song on YouTube:", e)
    return None

def download_video(youtube_link):
    global audio_urlbd, user_id, artist_name, album_cover, song_name
    try:
        video_id_temp = youtube_link.split('&')[0]
        video_id = video_id_temp.split('=')[-1]

        url = "https://youtube-media-downloader.p.rapidapi.com/v2/video/details"
        headers = {
            "X-RapidAPI-Key": "691cf07351mshdb1db153d036576p198512jsn2598991f7e02",
            "X-RapidAPI-Host": "youtube-media-downloader.p.rapidapi.com"
        }
        querystring = {"videoId": video_id}
        response = requests.get(url, headers=headers, params=querystring)

        if response.ok:
            data = response.json()
            if data and 'audios' in data and 'items' in data['audios'] and data['audios']['items']:
                audio_url = data['audios']['items'][0]['url']
                
                audio_urlbd=audio_url
                
                

                try:
                    save_playlist_to_database(user_id, artist_name, album_cover, song_name, duration_minutos)
                except Exception as e:
                    print("Error al guardar en la base de datos:", e)
                
                response = requests.get(audio_url)
                filename = os.path.join(app.root_path, 'static', 'audio', f"{song_name}.m4a")
                with open(filename, 'wb') as f:
                    f.write(response.content)
                return filename
            else:
                print("No se encontro un enlace de descarga de audio en la respuesta de la API.")
        else:
            print("Error al obtener el enlace de descarga del archivo de audio desde la API.")
        return None
    except Exception as e:
        print("Error al descargar el audio:", e)
        return None

def save_playlist_to_database(user_id, artist_name, album_cover, song_name, duration_minutos):
    global audio_urlbd

    if user_id:
        connection = mysql.connector.connect(host="localhost", user="root", passwd="", database="Users")
        cursor = connection.cursor()
        query = "INSERT INTO `playlists` (`user_id`, `artist_name`, `album_cover`, `song_name`, `duration_minutos`, `audio_url`) VALUES (%s, %s, %s, %s, %s, %s);"
        data = (user_id, artist_name, album_cover, song_name, duration_minutos, audio_urlbd)
        cursor.execute(query, data)
        connection.commit()
        connection.close()

@app.route('/dashboard')
def welcome():
    global audio_url, UserProfile, ProfilePicture
    
    time_period = random.choice(["day", "week", "month", "all_time"])
    artists = get_top_artists(time_period)
            
      
    
    
        
    
    return render_template('dashboard.html', audio_url=audio_url , song_name=song_name, album_cover=album_cover, artist_name=artist_name, UserProfile=UserProfile, ProfilePicture=ProfilePicture, artists=artists)
#--------------------------------Tranding---------------------------------










# la ruta 


@app.route('/trending')
def trendingPage():
    global audio_url, UserProfile, ProfilePicture
    
    time_period = random.choice(["day", "week", "month", "all_time"])
    artists = get_top_artists(time_period)
                
    recommended_albums = get_recommended_albums(time_period) 
    
    
    recommended_songs = get_recommended_songs(time_period)    
    
    return render_template('tranding.html', audio_url=audio_url , song_name=song_name, album_cover=album_cover, artist_name=artist_name, UserProfile=UserProfile, ProfilePicture=ProfilePicture, artists=artists, recommended_songs=recommended_songs, recommended_albums=recommended_albums)









#?---------------------------------funciones y rutas Flask anass----------------------------------------

@app.route("/")
def index():
    return render_template("Home.html")

@app.route("/login" , methods=["get"])
def login():
    return render_template("login.html")

@app.route("/Registerlogin", methods=["POST"])
def Registerlogin():
    global UserProfile, ProfilePicture
    message=""
    if request.method == "POST":
        username=request.form["Username"]
        password=request.form["password"]
        results=ConsultarUser(username,password)
        if len(results) ==0:
            message="Invalid username or password"
            return render_template("confirmationLogin.html", message=message)
        else:
            UserProfile = username
            ProfilePicture = results[0][11]
            
            return redirect(url_for('welcome'))

@app.route("/signUp", methods=["get"])
def signUp():
    Question=random.choice(Questions)
    return render_template("sign.html", Question=Question)

@app.route("/register", methods=["POST"])
def register():
    global ProfilePicture
    
    if request.method == "POST":
        name = request.form["Name"]
        lastname = request.form["Lastname"]
        age = request.form["age"]
        email = request.form["email"]
        username = request.form["Username"]
        gender = request.form["gender"]
        password = request.form["password"]
        question = request.form["Question"]
        answer = request.form["Answer"]
        profile_image_url = request.form.get('profile_image_url', 'https://github.com/RVDveloper/Anafael-Beats-V2/blob/main/static/img/_e1135106-ec32-445d-ad40-d9fb257f977e.jpg')
        connection = mysql.connector.connect(host="localhost", user="root", passwd="", database="Users")
        cursor = connection.cursor()
        query = "INSERT INTO `UserData` (`name`, `Lastname`, `age`, `password`, `email`, `Username`, `Gender`, `Question`, `Answer`, `profile_image_url`) \
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        cursor.execute(query, (name, lastname, age, password, email, username, gender, question, answer, profile_image_url))
        connection.commit()
        connection.close()
        
        ProfilePicture=profile_image_url

    return render_template("login.html")

@app.route("/ForgotPassword")
def ForgotPassword():
    return render_template("forgetPassword.html")

Answer=""

@app.route("/ConfirmationForgetPassword", methods=["POST"])
def ConfirmationForgetPassword():
    message=""
    if request.method=="POST":
        email=request.form["email"]
        Username=request.form["Username"]
        result=ConsultarEmail(Username,email)
        if len(result) == 0:
            message="This email or username is not correct"
            return render_template("confirmationForgetPasswordStep1.html", message=message)
        else:
            message="We hope you can answer this question"
            global Answer
            Answer=result[0][10]
            return render_template("confirmationForgetPasswordStep2.html", Question=result[0][9], message=message)
        
@app.route("/Settings",methods=["Get"])
def Settings():
    return render_template("settings.html")

@app.route("/Update",methods=["POST"])
def VerifyUpdate():
    if request.method=="POST":
        OldName=request.form["Name"]
        OldLastname=request.form["Lastname"]
        OldEmail=request.form["email"]
        OldUsername=request.form["Username"]
        result=ConsultarEmail(OldUsername,OldEmail)
        if len(result) == 0:
            message="This email or username is not correct"
            return render_template("confirmationForgetPasswordStep1.html", message=message)
        else:
            
            return render_template("Update.html", OldName=OldName, OldLastname=OldLastname, OldEmail=OldEmail, OldUsername=OldUsername)

@app.route("/ConfirmationUpdate", methods=["POST"])
def ConfirmationUpdate():
    if request.method=="POST":
        NewName=request.form["newName"]
        OldName=request.form["OldName"]
        NewLastname=request.form["NewLastname"]
        OldLastname=request.form["OldLastname"]
        NewAge=request.form["NewAge"]
        NewEmail=request.form["NewEmail"]
        OldEmail=request.form["OldEmail"]
        NewUsername=request.form["NewUsername"]
        OldUsername=request.form["OldUsername"]
        NewPassword=request.form["NewPassword"]
        connection=mysql.connector.connect(host="localhost", user="root", passwd="", database="Users")
        cursor = connection.cursor()
        query="UPDATE `UserData` SET `name`=%s, `Lastname`=%s, `age`=%s, `email`=%s, `Username`=%s, `password`=%s WHERE `email`=%s and `Username`=%s;"
        Values=(NewName, NewLastname, NewAge, NewEmail, NewUsername, NewPassword, OldEmail, OldUsername)
        cursor.execute(query, Values)
        connection.commit()
        connection.close()
        UserProfile = NewUsername
        message="Your data has been updated successfully"
        return render_template("ConfirmationUpdate.html", message=message , UserProfile=UserProfile)
       
        
@app.route("/AnswerForgetPassword", methods=["POST"])
def AnswerForgetPassword():
    if request.method == "POST":
        answer_user = request.form["AnswerUser"]
        answer_correct = Answer
        if answer_user == answer_correct:
            return render_template("restarPassword.html", AnswerCorrect=answer_correct)
        else:
            return render_template("confirmationForgetPasswordStep1.html", message="You have entered the wrong answer")

@app.route("/restarPassword", methods=["POST"])
def restarPassword():
    if request.method=="POST":
        password=request.form["password"]
        AnswerCorrect=request.form["AnswerCorrect"]
        connection=mysql.connector.connect(host="localhost", user="root", passwd="", database="Users")
        cursor = connection.cursor()
        query="UPDATE `UserData` SET `password`=%s WHERE `Answer`=%s;"
        cursor.execute(query, (password, AnswerCorrect))
        connection.commit()
        connection.close()
        message="Your password has been changed successfully"
        return render_template("PasswordChanged.html", message=message)
    
@app.route("/GameZone", methods=["GET"])
def gamePage():
    return render_template("Game.html")


@app.route('/playlist')
def playlist():
    global UserProfile

    
    playlists = get_user_playlists(user_id)

    
    playlist_range = f"1/{len(playlists)}" 

   
    selected_song_name = "Nombre de la canción seleccionada"

    
    selected_audio_url = None

    
    for playlist in playlists:
        if playlist[5] == selected_song_name:
            selected_audio_url = playlist[6]
            break

    print("Este es el valor de selected_audio_url en la función playlist:", selected_audio_url)

    return render_template('PlaylistPage.html', UserProfile=UserProfile, playlists=playlists, playlist_range=playlist_range, selected_song_name=selected_song_name, selected_audio_url=selected_audio_url)

@app.route('/update_selected_song', methods=['POST'])
def update_selected_song():
    global selected_song_name, selected_audio_url
    if request.method == 'POST':
        data = request.json
        selected_song_name = data.get('selected_song', '')
        selected_audio_url = data.get('selected_audio_url', '')
        print("este es el valor en la funcion update:", selected_audio_url)
        return jsonify({'message': 'Selected song updated successfully', 'selected_song': selected_song_name, 'selected_audio_url': selected_audio_url}), 200
    return jsonify({'error': 'Invalid request method'}), 405

#--------------------------------------game----------------------
dataframe= pd.read_csv("recurso/datos_artistas.csv")
Answer = ""
Puntos = 0
Preguntas_realizadas = 0
Pregunatas = {
    "Artista": "What is the Artist's Name ?",
    "Año": "What year was the song released?",
    "Album": "What is the album's name?",
    "Cancion": "What is the song's name?"
}
dataframe['Año de lanzamiento'] = dataframe['Año de lanzamiento'].astype(str)
dataframe.to_csv("datos_artistas_actualizado.csv", index=False)
def sacar_lista_artistas(dataframe):
    return dataframe["Artista"].unique().tolist()

def sacar_artista(lista_artistas):
    return random.choice(lista_artistas)

def sacar_lista_anos(artista):
    dataframe_artista = dataframe[dataframe["Artista"] == artista]
    return dataframe_artista["Año de lanzamiento"].unique().tolist()

def sacar_anio(lista_anos):
    return random.choice(lista_anos)

def sacar_album(artista, anio):
    dataframe_album = dataframe[(dataframe["Artista"] == artista) & (dataframe["Año de lanzamiento"] == anio)]
    return random.choice(dataframe_album["Álbum"].unique().tolist())

def sacar_cancion(artista, album):
    dataframe_cancion = dataframe[(dataframe["Artista"] == artista) & (dataframe["Álbum"] == album)]
    return random.choice(dataframe_cancion["Canción"].unique().tolist())

def sacar_url_artista(artista):
    dataframe_artista = dataframe[dataframe["Artista"] == artista]
    return dataframe_artista["URL Artista"].unique().tolist()[0]

def sacar_url_cancion(artista, album, cancion):
    dataframe_cancion = dataframe[(dataframe["Artista"] == artista) & (dataframe["Álbum"] == album) & (dataframe["Canción"] == cancion)]
    return dataframe_cancion["URL Canción"].unique().tolist()[0]

def datos():
    lista_artistas = sacar_lista_artistas(dataframe)
    artista = sacar_artista(lista_artistas)
    lista_anos = sacar_lista_anos(artista)
    anio = sacar_anio(lista_anos)
    album = sacar_album(artista, anio)
    cancion = sacar_cancion(artista, album)
    url_artista = sacar_url_artista(artista)
    url_cancion = sacar_url_cancion(artista, album, cancion)
    return artista, anio, album, cancion, url_artista, url_cancion

def sacar_datos(preguntas):
    question = random.choice(list(preguntas.values()))
    listaDatos=datos()
    if question == "What is the Artist's Name ?":
        
        guess_text = "Guess the Artist's Name"
        Answer = listaDatos[0]
        url_dato = listaDatos[4]
    elif question == "What year was the song released?":
        
        guess_text = "Guess the year the song was released"
        Answer = listaDatos[1]
        url_dato = listaDatos[5]
    elif question == "What is the album's name?":
        
        guess_text = "Guess the album's name"
        Answer = listaDatos[2]
        url_dato = listaDatos[5]
    elif question == "What is the song's name?":
        
        guess_text = "Guess the song's name"
        Answer = listaDatos[3]
        url_dato = listaDatos[5]
    return question, Answer, url_dato, guess_text

@app.route("/AboutGame")
def AboutGame():
    return render_template("AboutGame.html")

@app.route("/game")
def game():
    global Answer, Puntos, Preguntas_realizadas
    global Answer, Puntos, Preguntas_realizadas
    question, Answer, url_dato, guess_text= sacar_datos(Pregunatas)
    if Preguntas_realizadas < 10:
        return render_template("game.html", Question=question, UrlDato=url_dato, GuessText=guess_text, Puntos=Puntos)
    else:
       
        Preguntas_realizadas = 0
        message = f"End of Game. Your final score is {Puntos} points."
        Puntos = 0
        return render_template("End.html",message=message)

@app.route("/guess", methods=["POST"])
def guess():
    global Puntos, Preguntas_realizadas
    guess = request.form["guessInput"]
    Preguntas_realizadas += 1
    if guess == Answer:
        Puntos += 1
        message = f"Correct 😃! The answer was {Answer}. Your current score is {Puntos} points."
        return render_template("Result.html", Puntos=Puntos, message=message)
    else:
        message = f"Incorrect 😔! The answer was {Answer}. Your current score remains {Puntos} points."
        return render_template("Result.html", Answer=Answer, Puntos=Puntos, message=message)


#----------------------------lyrics------------------------------------------
def get_lyrics(artist, song_title):
    url = f"https://api.lyrics.ovh/v1/{artist}/{song_title}"
    response = requests.get(url)  # Aquí estaba el error
    
    if response.status_code == 200:
        data = response.json()
        lyrics = data.get("lyrics", "Lyrics not found")
        return lyrics
    else:
        return "Error: Unable to fetch lyrics"
@app.route("/lyrics", methods=["get"] )
def lyrics():
    return render_template("lyrics.html")

@app.route("/DatosLyrics", methods=["POST"])
def DatosLyrics():
    if request.method == "POST":
        Artist = request.form["Artist"]
        Music = request.form["Music"]
        lyrics = get_lyrics(Artist, Music)
        return render_template("ResultadoLyrics.html", lyrics=lyrics , Artist=Artist, Music=Music)

#----------------------------aboutus----------------------------------
@app.route("/About")
def About():
    return render_template("AboutUs.html") 



if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=True)


