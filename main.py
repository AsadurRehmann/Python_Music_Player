from tkinter import *
import pygame
from tkinter import filedialog, messagebox
import os
import json
import time
from mutagen.mp3 import MP3
import tkinter.ttk as ttk
from tkinter import font as tkfont
import random  # For shuffle

pygame.mixer.init()

window = Tk()
window.title('Music Player')
window.geometry('1150x750')

# Theme 
style = ttk.Style()
style.theme_use('classic')  # alt,default, classic,vista

# Custom fonts
title_font = tkfont.Font(family="Arial", size=16, weight="bold")
button_font = tkfont.Font(family="Arial", size=12)
label_font = tkfont.Font(family="Arial", size=12)

playlist = [] 
playlists = {}  
most_listened = {} 
current_song_index = 0
paused = False
playback_position = 0
stopped = False
slider_dragging = False
current_time = 0
real_time=0

# Load saved progress
if os.path.exists('music_player_progress.json'):
    try:
        with open('music_player_progress.json', 'r') as f:
            saved_data = json.load(f)
            playlist = saved_data.get('playlist', [])
            playlists = saved_data.get('playlists', {})
            most_listened = saved_data.get('most_listened', {})
            current_song_index = saved_data.get('current_song_index', 0)
            playback_position = saved_data.get('playback_position', 0)
    except json.JSONDecodeError:
        print("Error: Corrupt JSON file. Starting fresh.")
        playlist = []
        playlists = {}
        most_listened = {}
        current_song_index = 0
        playback_position = 0

# song to main plalist
def adding_songs():
    songs = filedialog.askopenfilenames(initialdir='songs/', title='Choose songs', filetypes=(("mp3 files", "*.mp3"),))
    for song in songs:
        playlist.append(song)
        song_name = os.path.basename(song).replace(".mp3", "")
        main_playlist_box.insert(END, song_name)

# Play a song 
def play():
    global current_song_index, playback_position, stopped, paused, real_time
    if playlist:
        stopped = False
        
        if paused:
            song = playlist[current_song_index]
            pygame.mixer.music.load(song)
            pygame.mixer.music.play(start=playback_position)
            paused = False
        else:
            real_time = 0
            playback_position = 0
            song = playlist[current_song_index]
            pygame.mixer.music.load(song)
            pygame.mixer.music.play(loops=0)
        
        main_playlist_box.selection_clear(0, END)
        main_playlist_box.activate(current_song_index)
        main_playlist_box.selection_set(current_song_index)
#update most listened songs and time
        update_most_listened(song)
        play_time()

def shuffle_playlist():
    global playlist, current_song_index
    if playlist:
        random.shuffle(playlist)  
        main_playlist_box.delete(0, END)  
        for song in playlist:  
            song_name = os.path.basename(song).replace(".mp3", "")
            main_playlist_box.insert(END, song_name)
        current_song_index = 0  
        play()  

# update most listened songs
def update_most_listened(song):
    song_name = os.path.basename(song).replace(".mp3", "")
    most_listened[song_name] = most_listened.get(song_name, 0) + 1
    update_most_listened_box()

def update_most_listened_box():
    most_listened_box.delete(0, END)
    sorted_songs = sorted(most_listened.items(), key=lambda x: x[1], reverse=True)
    for song, count in sorted_songs:
        most_listened_box.insert(END, f"{song}  ({count} plays)")

# Add songs from most listened
def add_from_most_listened():
    selected_song_indices = most_listened_box.curselection()
    selected_playlist = playlist_box.get(ACTIVE)

    if selected_song_indices and selected_playlist:
        for selected_song_index in selected_song_indices:
            song_name = most_listened_box.get(selected_song_index).split(" (")[0].strip() 

            found = False
            for song_path in playlist:
                base_name = os.path.basename(song_path).replace(".mp3", "").strip() 
                if base_name == song_name:
                    if song_path not in playlists.get(selected_playlist, []):
                        playlists.setdefault(selected_playlist, []).append(song_path)
                        update_selected_playlist_box(selected_playlist)
                        messagebox.showinfo("Success", f"'{song_name}' added to '{selected_playlist}'!")
                    else:
                        messagebox.showwarning("Warning", f"'{song_name}' is already in '{selected_playlist}'!")
                    found = True
                    break
            if not found:
                messagebox.showwarning("Warning", f"'{song_name}' not found in the main playlist. Add it to the main playlist first.")
    elif not selected_playlist:
        messagebox.showwarning("Warning", "Please select a playlist.")
    elif not selected_song_indices:
        messagebox.showwarning("Warning", "Please select a song from the most listened list.")
   

# Playlist 
def create_playlist():
    playlist_name = playlist_name_entry.get()
    if playlist_name:
        if playlist_name not in playlists:
            playlists[playlist_name] = []
            playlist_box.insert(END, playlist_name)
            playlist_name_entry.delete(0, END)
        else:
            messagebox.showwarning("Error", "Playlist already exists!")

def add_to_playlist():
    selected_playlist = playlist_box.get(ACTIVE)
    selected_song_indices = main_playlist_box.curselection()
    if selected_playlist and selected_song_indices:
        selected_song_index = selected_song_indices[0]
        song_path = playlist[selected_song_index]  
        playlists[selected_playlist].append(song_path)
        update_selected_playlist_box(selected_playlist)
        messagebox.showinfo("Success", "Song added to playlist!")

def update_selected_playlist_box(playlist_name):
    selected_playlist_songs_box.delete(0, END)
    for song_path in playlists[playlist_name]:
        song_name = os.path.basename(song_path).replace(".mp3", "")
        selected_playlist_songs_box.insert(END, song_name)

def on_playlist_select(event):
    selected_playlist = playlist_box.get(ACTIVE)
    if selected_playlist:
        update_selected_playlist_box(selected_playlist)

# Selected playlist songs
def play_selected_playlist_song():
    global current_song_index, playback_position
    selected_playlist = playlist_box.get(ACTIVE)
    selected_song_indices = selected_playlist_songs_box.curselection()
    if selected_playlist and selected_song_indices:
        selected_song_index = selected_song_indices[0]
        song_path = playlists[selected_playlist][selected_song_index]
        pygame.mixer.music.load(song_path)
        pygame.mixer.music.play()
        update_most_listened(song_path)

        current_song_index = playlist.index(song_path)
        playback_position = 0

def remove_from_playlist():
    selected_playlist = playlist_box.get(ACTIVE)
    selected_song_indices = selected_playlist_songs_box.curselection()
    if selected_playlist and selected_song_indices:
        selected_song_index = selected_song_indices[0]
        del playlists[selected_playlist][selected_song_index]
        update_selected_playlist_box(selected_playlist)
    selected_playlist_songs_box.delete(0, END)
    update_selected_playlist_box(selected_playlist)

def delete_playlist():
    selected_playlist = playlist_box.get(ACTIVE)
    if selected_playlist:
        del playlists[selected_playlist]
        playlist_box.delete(ACTIVE)
        selected_playlist_songs_box.delete(0, END)
        messagebox.showinfo("Success", "Playlist deleted!")

# Save progress
def save_progress():
    global playback_position
    if playlist:
        playback_position = pygame.mixer.music.get_pos() / 1000
    with open('music_player_progress.json', 'w') as f:
        json.dump({
            'playlist': playlist,
            'playlists': playlists,
            'most_listened': most_listened,
            'current_song_index': current_song_index,
            'playback_position': playback_position
        }, f)
    window.destroy()

def prevsong():
    global current_song_index, playback_position
    if playlist:
        current_song_index = (current_song_index - 1) % len(playlist)
        playback_position = 0
        play()

def nextsong():
    global current_song_index, playback_position
    if playlist:
        current_song_index = (current_song_index + 1) % len(playlist)
        playback_position = 0
        play()

def pause():
    global paused
    if playlist:
        if paused:
            pygame.mixer.music.unpause()  # Resume playback without restarting
            paused = False
            play_time()  # Call play_time to update the slider and elapsed time
        else:
            pygame.mixer.music.pause()  # Pause without stopping the song
            paused = True


def stop():
    global stopped, paused, playback_position, real_time, playlists
    if playlist:
        pygame.mixer.music.stop()
        stopped = True
        paused = False  
        playback_position = 0 
        real_time = 0
        my_slider.set(0)  
        elapsed_time_label.config(text="00:00 / 00:00") 
        
        # Clear playlists to save memory
        playlists.clear()
        playlist_box.delete(0, END)
        selected_playlist_songs_box.delete(0, END)
        messagebox.showinfo("Memory Cleared", "All playlists have been deleted to save memory.")


# Slider interaction
def start_slide(event):
    global slider_dragging
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()
    slider_dragging = True

def end_slide(event):
    global slider_dragging, playback_position
    slider_dragging = False
    new_position = float(my_slider.get())
    
    if playlist:
        song = playlist[current_song_index]
        pygame.mixer.music.load(song)
        pygame.mixer.music.play(start=new_position)
        playback_position = new_position

def slide(x):
    if slider_dragging and playlist:
        current_time = float(my_slider.get())
        converted_current_time = time.strftime('%M:%S', time.gmtime(current_time))
        converted_song_length = time.strftime('%M:%S', time.gmtime(current_song_length))
        elapsed_time_label.config(text=f' {converted_current_time} / {converted_song_length}')

def play_time():
    global stopped, paused, playback_position, real_time, current_song_length

    if stopped or not playlist or paused:  # Respect the paused state
        return

    if current_song_index < len(playlist):
        song = playlist[current_song_index]
        try:
            song_mut = MP3(song)
            current_song_length = song_mut.info.length
        except Exception as e:  
            print(f"Error loading MP3 info: {e}")
            current_song_length = 0  
            
        if not slider_dragging:
            if pygame.mixer.music.get_busy():
                current_pos = pygame.mixer.music.get_pos() / 1000
                if current_pos >= 0:
                    real_time = playback_position + current_pos
                else:
                    real_time = playback_position

                my_slider.config(to=current_song_length)
                my_slider.set(real_time)

                converted_current_time = time.strftime('%M:%S', time.gmtime(real_time))
                converted_song_length = time.strftime('%M:%S', time.gmtime(current_song_length))
                elapsed_time_label.config(text=f' {converted_current_time} / {converted_song_length}')

                if real_time >= current_song_length and not paused:  # Respect the paused state
                    nextsong()  # Play the next song 
                    return 
            else:
                nextsong()  
                return  

    elapsed_time_label.after(1000, play_time) 
#to play a slected song 
def main_playlist_selected(event): 
    global current_song_index
    try:
        current_song_index = main_playlist_box.curselection()[0]

        play()
    except IndexError: 
        pass

# Main UI Layout
master_frame = Frame(window)
master_frame.pack(pady=20)

left_frame = Frame(window, bg='#f0f0f0')
left_frame.pack(side=LEFT, fill=Y, padx=10)

middle_frame = Frame(window, bg='#f0f0f0')
middle_frame.pack(side=LEFT, fill=Y, padx=10)

right_frame = Frame(window, bg='#f0f0f0')
right_frame.pack(side=LEFT, fill=Y, padx=10)

# Most Listened Section
most_listened_label = Label(left_frame, text="Most Listened", font=title_font, bg='#f0f0f0')
most_listened_label.pack()
most_listened_box = Listbox(left_frame, bg='white', fg='black', width=40, height=15)
most_listened_box.pack()
Button(left_frame, text="Add to Playlist", command=add_from_most_listened, font=button_font, bg='#2196F3', fg='white').pack(pady=5)

# Main Playlist Section
main_playlist_box = Listbox(middle_frame, bg='white', fg='black', width=40, height=15)
main_playlist_box.pack()
main_playlist_box.bind('<<ListboxSelect>>', main_playlist_selected)  # Bind the event!
# Playlists Section
playlist_label = Label(right_frame, text="Playlists", font=title_font, bg='#f0f0f0')
playlist_label.pack()
playlist_box = Listbox(right_frame, bg='white', fg='black', width=20, height=5)
playlist_box.pack()
playlist_box.bind('<<ListboxSelect>>', on_playlist_select)

playlist_name_entry = Entry(right_frame, font=label_font)
playlist_name_entry.pack(pady=5)

Button(right_frame, text="Create Playlist", command=create_playlist, font=button_font, bg='#4CAF50', fg='white').pack(pady=5)
Button(right_frame, text="Add to Playlist", command=add_to_playlist, font=button_font, bg='#2196F3', fg='white').pack(pady=5)

selected_playlist_label = Label(right_frame, text="Songs in Playlist", font=title_font, bg='#f0f0f0')
selected_playlist_label.pack()
selected_playlist_songs_box = Listbox(right_frame, bg='white', fg='black', width=40, height=15)
selected_playlist_songs_box.pack()

Button(right_frame, text="Play Selected", command=play_selected_playlist_song, font=button_font, bg='#FF9800', fg='white').pack(pady=5)
Button(right_frame, text="Remove from Playlist", command=remove_from_playlist, font=button_font, bg='#F44336', fg='white').pack(pady=5)
Button(right_frame, text="Delete Playlist", command=delete_playlist, font=button_font, bg='#9E9E9E', fg='white').pack(pady=5)

# Playback Controls
controls_frame = Frame(middle_frame, bg='#f0f0f0')
controls_frame.pack(pady=10)
Button(controls_frame, text="⏮ Previous", command=prevsong, font=button_font, bg='#607D8B', fg='white').grid(row=0, column=0, padx=5)
Button(controls_frame, text="▶️ Play", command=play, font=button_font, bg='#4CAF50', fg='white').grid(row=0, column=1, padx=5)
Button(controls_frame, text="⏸ Pause", command=pause, font=button_font, bg='#FF9800', fg='white').grid(row=0, column=2, padx=5)
Button(controls_frame, text="⏹ Stop", command=stop, font=button_font, bg='#F44336', fg='white').grid(row=0, column=3, padx=5) # Stop button
Button(controls_frame, text="⏭ Next", command=nextsong, font=button_font, bg='#607D8B', fg='white').grid(row=0, column=4, padx=5)
Button(controls_frame, text="🔀 Shuffle", command=shuffle_playlist, font=button_font, bg='#9C27B0', fg='white').grid(row=0, column=5, padx=5)

# Music Position Slider and Elapsed Time
slider_frame = Frame(controls_frame, bg='#f0f0f0')
slider_frame.grid(row=1, column=0, columnspan=5, pady=10)

my_slider = ttk.Scale(slider_frame, from_=0, to=100, orient=HORIZONTAL, value=0, command=slide, length=300)
my_slider.pack(side=LEFT, padx=5)
my_slider.bind("<ButtonPress-1>", start_slide)  # Start dragging
my_slider.bind("<ButtonRelease-1>", end_slide)  # End dragging

elapsed_time_label = Label(slider_frame, text="00:00 / 00:00", font=label_font, bg='#f0f0f0')
elapsed_time_label.pack(side=LEFT, padx=5)

# Menu Bar
song_menu = Menu(window)
window.config(menu=song_menu)
add_song = Menu(song_menu, tearoff=False)
song_menu.add_cascade(label='Menu', menu=add_song)
add_song.add_command(label='Add songs', command=adding_songs)

for song in playlist:
    song_name = os.path.basename(song).replace(".mp3", "")
    main_playlist_box.insert(END, song_name)

for playlist_name in playlists:
    playlist_box.insert(END, playlist_name)

update_most_listened_box()
window.protocol("WM_DELETE_WINDOW", save_progress)
window.mainloop()