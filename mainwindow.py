from PyQt5.QtCore import QSize, QRect, QPropertyAnimation, QTimeLine, QTimer, QThread, QPoint
from PyQt5.QtGui import QIcon, QPixmap, QTransform
import functools
from time import sleep
import random
from random import randint
import threading

from PyQt5.QtWidgets import QSlider, QTableWidgetItem, QGraphicsOpacityEffect
import requests

import AudioApp
from AudioApp import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal as Signal

from bs4 import BeautifulSoup
import pafy
import youtube_dl as yt
import subprocess
# from win32api import GetSystemMetrics
import time
import os
import vlc

import json


patho = os.getcwd()
myfil = patho + r'\playlist.json'
with open(myfil, "r+") as outfile:
    newList = json.load(outfile)
playLists = newList

patho = os.getcwd()
myfil = patho + r'\playListDict.json'
with open(myfil, "r+") as outfile:
    newDict = json.load(outfile)
playListDict = newDict

arrowPixmap = None
tresDotPixmap = None
droppedDown = False

whatSearch = ''

items_dictionary = (('', ''), ('', ''), ('', ''))

songPlaying = False
songPlayingUrl = ''
songPlayingName = ''
songsPlayed = []

volume = 50


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):

        global volume
        super(MainWindow, self).__init__()
        self.setupUi(self)

        # self.setWindowFlag(Qt.FramelessWindowHint)

        with open('style.css', 'r') as styleh:
            self.selectPlaylistAddTo.setStyleSheet(styleh.read())
            self.addSongFrame.setStyleSheet(styleh.read())

        gEffect = QGraphicsOpacityEffect()
        gEffect.setOpacity(0.9)
        self.addSongFrame.setGraphicsEffect(gEffect)

        self.selectPlaylistAddTo.clear()

        self.startSignal()

        self.addSongFrame.hide()

        self.tresDotDict = {}
        self.optDotDict = {}
        self.playDict = {}
        self.likedDict = {}
        self.playListButtonDict = {}
        self.playListDictTable = {}
        self.resultsSearch = []
        self.currentOptSong = ''
        self.currentOptUrl = ''
        self.currentYtUrl = ''
        self.currentOptVidUrl = ''
        self.listButtonDict = {}
        self.globalPlayList = []
        self.newPlay = False
        self.columnButtonDict = {}
        self.columnDictTable = {}
        self.activeTable = None
        self.previous_songs = []
        self.current_playlist_start = 0
        self.uploading = True
        self.vid_on = False
        self.vid_player = vlc.MediaPlayer()

        self.threads = 50

        self.current_loop = 'NONE' # 'PLAYLIST', 'SONG'

        self.currentSongInd = -1

        self.pauseDown()
        self.dropDownFrame.setGeometry(QtCore.QRect(20, 31, 120, 23))
        self.firstOption.mousePressEvent = functools.partial(self.firstOptionPressed)
        self.secondOption.mousePressEvent = functools.partial(self.secondOptionPressed)
        self.thirdOption.mousePressEvent = functools.partial(self.thirdOptionPressed)
        self.firstOption.setText('')
        self.secondOption.setText('')
        self.thirdOption.setText('')

        self.addSongToPlaylistBtn.clicked.connect(self.addSong)

        self.exitAddSong.clicked.connect(self.exitAddSongFrame)

        self.optionsDropDownFrame.hide()

        self.createPlaylistGet.hide()
        self.createPlaylistButton.hide()

        self.playlistsTable.clear()
        self.playlistsTable.setRowCount(1)
        self.playlistsTable.setItem(0, 0, QTableWidgetItem("No Playlists Right Now"))

        self.playlistsTable.hide()

        global arrowPixmap
        global tresDotPixmap

        self.playlistsButton.clicked.connect(self.playlistBtnPressed)

        self.updatePlayLists()
        self.updatePlayListsVisual()

        self.createPlaylistButton.clicked.connect(self.pressedCreatePlaylist)

        arrowPixmap = QPixmap('Arrow.png')
        playButtonPixmap = QPixmap('playButton.png')
        pauseButtonPixmap = QPixmap('pauseButton.png')
        threeDotPixmap = QPixmap('tresCircle.png')
        tresDotPixmap = QPixmap('tresCircle.png')
        self.minusButtonPixmap = QPixmap('minusButton.png')
        skipPixmap = QPixmap('skip.png')
        backPixmap = QPixmap('back.png')
        self.loop_deactivated_pixmap = QPixmap('loop_deactivated.png')
        self.loop_playlist_activated_pixmap = QPixmap('loop_playlist_activated.png')
        self.loop_song_pixmap = QPixmap('loop_song.png')
        self.vid_button_pixmap = QPixmap('vid_button.png')

        self.vidButton.setIcon(QIcon(self.vid_button_pixmap))

        self.dropDownArrowBtn.setIcon(QIcon(arrowPixmap))
        self.dropDownArrowBtn.clicked.connect(self.dropDown)

        self.skipButton.setIcon(QIcon(skipPixmap))
        self.backButton.setIcon(QIcon(backPixmap))
        self.loopButton.setIcon(QIcon(self.loop_deactivated_pixmap))
        self.loopButton.clicked.connect(self.loopButtonPressed)

        self.playButton.setIcon(QIcon(playButtonPixmap))
        playButtonSize = QSize()
        playButtonSize.setWidth(35)
        playButtonSize.setHeight(35)
        self.playButton.setIconSize(playButtonSize)
        self.playButton.clicked.connect(self.pressedPlay)

        self.pauseButton.setIcon(QIcon(pauseButtonPixmap))
        pauseButtonSize = QSize()
        pauseButtonSize.setWidth(35)
        pauseButtonSize.setHeight(35)
        self.pauseButton.setIconSize(pauseButtonSize)
        self.pauseButton.clicked.connect(self.pressedPause)

        self.searchBar.returnPressed.connect(self.onPressedSearchBar)

        self.createPlaylistGet.returnPressed.connect(self.addPlaylistLine)

        self.updatePlayListsVisual()
        self.updateMinus()

        self.hideAllPlaylists()
        self.hideAllMinus()
        self.updateAll()

        self.updateAddSongPlaylistList()

        self.updatePlayListTables()

        self.volumeSlider.setTickInterval(12)
        self.volumeSlider.setMaximum(130)
        self.volumeSlider.setMinimum(0)
        self.volumeSlider.setValue(65)
        volume = self.volumeSlider.value()
        self.volumeSlider.sliderMoved.connect(self.updateVolume)

        self.volumeSlider.sliderMoved.connect(self.updateVolume)

        self.deletePlaylistButton = QtWidgets.QPushButton(self.centralwidget)
        self.deletePlaylistButton.setGeometry(QtCore.QRect(265, 475, 125, 30))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.deletePlaylistButton.setFont(font)
        self.deletePlaylistButton.setStyleSheet("background-color: red;\n"
                                                "color: white;\n"
                                                "border-style: solid;\n"
                                                "border-width: 2px;\n"
                                                "border-radius: 12px;\n"
                                                "border-color: red;")
        self.deletePlaylistButton.setObjectName("createPlaylistButton")
        self.deletePlaylistButton.setText("Remove Playlist")
        self.deletePlaylistButton.clicked.connect(self.pressedDeletePlaylist)

        self.deletePlaylistGet = QtWidgets.QLineEdit(self.centralwidget)
        self.deletePlaylistGet.setGeometry(QtCore.QRect(265, 475, 125, 30))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.deletePlaylistGet.setFont(font)
        self.deletePlaylistGet.setStyleSheet("background-color: red;\n"
                                             "color: white;\n"
                                             "border-style: solid;\n"
                                             "border-color: transparent;\n"
                                             "border-width: 2px;\n"
                                             "border-radius: 12px;\n"
                                             "border-color: red;")
        self.deletePlaylistGet.setObjectName("createPlaylistGet")
        self.deletePlaylistGet.returnPressed.connect(self.deletePlaylistLine)

        self.skipButton.clicked.connect(self.skip)
        self.backButton.clicked.connect(self.back)

        self.deletePlaylistButton.hide()
        self.deletePlaylistGet.hide()

        self.uploadingSongsLabel.setText('Gathering Songs...')
        self.uploadingSongsFrame.show()
        self.startUpload()

        self.vidButton.clicked.connect(self.vid_button_pressed)

        self.timeSlider.sliderReleased.connect(self.updateTime)

        self.startTimeSignal()

        self.oldPos = self.pos()

    def vid_button_pressed(self):
        try:
            state = self.songPlayingVlc.get_state()
            print('hi')
            if not self.vid_on:
                print(self.globalPlayList[self.currentSongInd])
                self.vid_player = vlc.MediaPlayer(self.globalPlayList[self.currentSongInd][3])

                cr_time = self.songPlayingVlc.get_time()
                self.vid_player.play()
                self.vid_player.set_time(cr_time)
                vid_time = self.vid_player.get_time()
                self.vid_on = True
            else:
                self.vid_player.stop()
                self.vid_player = None
                self.vid_on = False
        except:
            print('No Song Playing Right Now')

    # def mousePressEvent(self, event):
    #     self.oldPos = event.globalPos()
    #
    # def mouseMoveEvent(self, event):
    #     delta = QPoint(event.globalPos() - self.oldPos)
    #     #print(delta)
    #     self.move(self.x() + delta.x(), self.y() + delta.y())
    #     self.oldPos = event.globalPos()

    def skip(self):
        try:
            self.songPlayingVlc.stop()

            for val in self.globalPlayList:
                print(val[0])
        except:
            print('Nothing to skip')

    def back(self):
        try:
            if self.currentSongInd > 0:
                self.currentSongInd -= 2
                self.songPlayingVlc.stop()
                self.songPlayingVlc.pressedPause()
            else:
                print('No Previous Songs')
        except:
            print('No Previous Songs')


    def deletePlaylistLine(self):
        if self.deletePlaylistGet.text() != '':
            try:
                currentDir = os.getcwd()
                myfile = currentDir + r'\playlist.json'
                playLists.remove(self.deletePlaylistGet.text())
                playListDict.pop(self.deletePlaylistGet.text())
                self.updatePlayListDict()
                with open(myfile, "w+") as outfil:
                    json.dump(playLists, outfil)
                self.updatePlayLists()
                self.updatePlayListsVisual()
                self.deletePlaylistGet.clear()
                self.deletePlaylistGet.hide()
                self.deletePlaylistButton.show()
                self.updateMinus()
                self.updatePlayListTablesMinus()
                self.updatePlayListTables()
                self.hideAllMinus()
            except:
                print('Not a valid playlist')
                self.deletePlaylistGet.clear()
                self.deletePlaylistGet.hide()
                self.deletePlaylistButton.show()
        elif self.deletePlaylistGet.text() == '':
            self.deletePlaylistGet.hide()
            self.deletePlaylistButton.show()
        else:
            print('Not a valid playlist')

    def loopButtonPressed(self):
        if self.current_loop == 'NONE':
            self.current_loop = 'PLAYLIST'
            self.loopButton.setIcon(QIcon(self.loop_playlist_activated_pixmap))

        elif self.current_loop == 'PLAYLIST':
            self.current_loop = 'SONG'
            self.loopButton.setIcon(QIcon(self.loop_song_pixmap))
        else:
            self.current_loop = 'NONE'
            self.loopButton.setIcon(QIcon(self.loop_deactivated_pixmap))

    def pressedDeletePlaylist(self):
        self.createPlaylistButton.show()
        self.createPlaylistGet.clear()
        self.createPlaylistGet.hide()
        self.deletePlaylistButton.hide()
        self.deletePlaylistGet.show()

    def pressedOpt(self, na, va, ta, qa):
        self.addSongFrame.show()
        self.updateAddSongPlaylistList()
        self.currentOptSong = na
        self.currentOptUrl = va
        self.currentYtUrl = ta
        self.currentOptVidUrl = qa

    def updateAddSongPlaylistList(self):
        self.selectPlaylistAddTo.clear()
        for index in range(len(playLists)):
            self.selectPlaylistAddTo.addItem(playLists[index])

    def addSong(self):
        playName = self.selectPlaylistAddTo.itemText(self.selectPlaylistAddTo.currentIndex())
        for name in playListDict:
            length = len(playListDict[name])
            if name == playName:
                playListDict[name].update({length: (self.currentOptSong, self.currentOptUrl, self.currentYtUrl, self.currentOptVidUrl)})
                break
            else:
                pass

        self.updatePlayLists()
        self.updateMinus()
        self.updatePlayListTablesMinus()
        self.updatePlayListTables()

        self.addSongFrame.hide()


    def exitAddSongFrame(self):
        self.addSongFrame.hide()


    def startSignal(self):
        self.t = QTimer()
        self.t.timeout.connect(self.checkPlayerState)
        self.t.setInterval(300)
        self.t.start()

    def startUpload(self):
        self.u = QTimer()
        self.u.timeout.connect(self.multithread_update)
        self.u.setInterval(1000)
        self.u.start()
        self.uploadingSongsFrame.show()

    def endUpload(self):
        self.uploadingSongsFrame.hide()
        self.u.stop()

    def update_link(self, playlist, song, increment):
        new_link = self.new_url_aud(playListDict[playlist][song][2])
        playListDict[playlist][song][1] = new_link
        val = self.uploadingProgressBar.value()
        self.uploadingProgressBar.setValue(val + increment)

    # def update_links(self):
    #     if self.uploading:
    #         self.uploadingProgressBar.setValue(0)
    #         songs = 0
    #         for playlist in playListDict:
    #             for song in playListDict[playlist]:
    #                 songs += 1
    #
    #         try:
    #             increment = int(100/songs)
    #
    #             for playlist in playListDict:
    #                 for song in playListDict[playlist]:
    #                     new_link = self.new_url(playListDict[playlist][song][2])
    #                     playListDict[playlist][song][1] = new_link
    #                     val = self.uploadingProgressBar.value()
    #                     self.uploadingProgressBar.setValue(val + increment)
    #                     print(playListDict[playlist][song][0])
    #             self.uploading = False
    #             self.endUpload()
    #         except ZeroDivisionError:
    #             self.uploading = False
    #             self.endUpload()

    def multithread_update(self):
        self.uploadingProgressBar.setValue(0)
        songs = 0
        for playlist in playListDict:
            for song in playListDict[playlist]:
                songs += 1
        try:
            increment = int(100 / songs)

            for playlist in playListDict:
                for song in playListDict[playlist]:
                    started = False
                    while not started:
                        if threading.active_count() <= self.threads:
                            threading.Thread(target=self.update_link, args=(playlist, song, increment,)).start()
                            started = True

            self.uploading = False
            self.endUpload()
        except ZeroDivisionError:
            self.uploading = False
            self.endUpload()

    def startTimeSignal(self):
        self.r = QTimer()
        self.r.timeout.connect(self.check_time)
        self.r.setInterval(300)
        self.r.start()

    def endTimeSignal(self):
        self.r.stop()

    def check_time(self):
        try:
            state = str(self.songPlayingVlc.get_state())
            song_length_seconds = int(self.songPlayingVlc.get_length() / 1000)
        except:
            state = ''
            song_length_seconds = 0

        song_length_mins = int(song_length_seconds / 60)
        song_length_secs = int(song_length_seconds % 60)

        if song_length_secs < 10:
            song_length = f'{song_length_mins}:0{song_length_secs}'
        else:
            song_length = f'{song_length_mins}:{song_length_secs}'

        self.timeLabelEnd.setText(song_length)

        try:
            state = str(self.songPlayingVlc.get_state())
            current_seconds_total = int(self.songPlayingVlc.get_time() / 1000)
        except:
            state = ''
            current_seconds_total = 0

        current_mins = int(current_seconds_total / 60)
        current_secs = int(current_seconds_total % 60)

        if current_secs < 10:
            song_time = f'{current_mins}:0{current_secs}'
        else:
            song_time = f'{current_mins}:{current_secs}'

        self.timeLabel.setText(song_time)

        if state == 'State.Playing' or state == 'State.Paused':
            self.timeSlider.setTickInterval(1)
            self.timeSlider.setMaximum(song_length_seconds)
            self.timeSlider.setMinimum(0)
            self.timeSlider.setValue(current_seconds_total)
        else:
            self.timeLabel.setText('0:00')
            self.timeSlider.setValue(0)

    def updateTime(self):
        try:
            self.songPlayingVlc.get_state()
            self.endTimeSignal()
            c_seconds_total = self.timeSlider.value()
            self.songPlayingVlc.set_time(c_seconds_total*1000)
            self.startTimeSignal()
        except AttributeError:
            pass

    def startSignalPlayListsChanged(self):
        self.p = QTimer()
        self.p.timeout.connect(self.playlistWasChanged)
        self.p.setInterval(300)
        self.p.start()

    def playlistWasChanged(self):
        try:
            self.songPlayingVlc.stop()
            self.currentSongLabel.setText('')
        except:
            print('No Player To Stop')

        self.songPlayingVlc = vlc.MediaPlayer(self.globalPlayList[self.currentSongInd][1])
        self.songPlayingVlc.play()
        self.currentSongLabel.setText(self.globalPlayList[self.currentSongInd][0])
        self.pressedPlay()


    def updateAll(self):
        self.updatePlayListDict()
        self.updatePlayLists()
        self.updatePlayListsVisual()
        self.updatePlayListTables()
        self.updatePlayListsVisual()
        self.updateMinus()
        self.updatePlayListTablesMinus()
        self.updatePlayListTablesMinus()
        self.hideAllPlaylists()
        self.hideAllMinus()


    def updatePlayListTables(self):
        for ind in range(len(self.playListDictTable)):
            rowCount = len(playListDict[playLists[ind]])
            self.playListDictTable[playLists[ind]].clear()
            self.playListDictTable[playLists[ind]].setRowCount(rowCount)
            self.playListDictTable[playLists[ind]].setColumnCount(1)
            self.listButtonDict[ind] = {}
            for index in range(rowCount):
                i = int(index)
                self.listButtonDict[ind][i] = QtWidgets.QPushButton()
                self.listButtonDict[ind][i].setGeometry(QtCore.QRect(0, 0, 40, 40))
                self.listButtonDict[ind][i].setStyleSheet("border: 0px solid red;\n"
                                                          "color: white;\n"
                                                          "background-color: transparent;\n"
                                                          "font-size: 14px;\n"
                                                          "Text-align: left;\n"
                                                          "font: bold;")
                self.listButtonDict[ind][i].setObjectName("playlistTableBtn")
                self.playListDictTable[playLists[ind]].setCellWidget(index, 0, self.listButtonDict[ind][i])
                self.listButtonDict[ind][i].setText(playListDict[playLists[ind]][i][0])
        self.updatePlayListTablesClicked()

    def updatePlayListTablesMinus(self):
        for ind in range(len(self.playListDictTable)):
            columnCount = 1
            rowCount = len(playListDict[playLists[ind]])
            self.columnDictTable[playLists[ind]].setRowCount(rowCount)
            self.columnDictTable[playLists[ind]].setColumnCount(columnCount)
            self.columnButtonDict[ind] = {}
            for index in range(rowCount):
                i = int(index)
                self.columnButtonDict[ind][i] = QtWidgets.QPushButton()
                self.columnButtonDict[ind][i].setGeometry(QtCore.QRect(0, 0, 10, 10))
                self.columnButtonDict[ind][i].setStyleSheet("border: 0px solid red;\n"
                                                         "color: white;\n"
                                                         "background-color: transparent;\n"
                                                         "font-size: 14px;\n"
                                                         "Text-align: left;\n"
                                                         "font: bold;\n"
                                                         "padding-left: 50px;")
                self.columnButtonDict[ind][i].setIcon(QIcon(self.minusButtonPixmap))
                addButtonSize = QSize()
                addButtonSize.setWidth(35)
                addButtonSize.setHeight(35)
                self.columnButtonDict[ind][i].setIconSize(addButtonSize)
                self.columnButtonDict[ind][i].setObjectName("playlistTableBtn")
                self.columnDictTable[playLists[ind]].setCellWidget(index, 0, self.columnButtonDict[ind][i])
                self.columnButtonDict[ind][i].clicked.connect(lambda state, x=ind, y=i: self.removeSongFromDict(x, y))

    def removeSongFromDict(self, ind, i):
        playListDict[playLists[ind]].pop(i)
        self.updatePlayListDict()
        self.playListDictTable[playLists[ind]].clear()
        self.columnDictTable[playLists[ind]].clear()
        self.updatePlayListTables()
        self.updatePlayListTablesMinus()


    def updatePlayListTablesClicked(self):
        for ind in range(len(self.playListDictTable)):
            rowCount = len(playListDict[playLists[ind]])
            for index in range(rowCount):
                i = int(index)
                self.listButtonDict[ind][i].clicked.connect(lambda state, x=ind, y=i: self.addToGlobalPlaylist(x, y))


    def addToGlobalSong(self, na, va):
        self.globalPlayList.append((na, va))
        # print(self.globalPlayList)

    # def addToGlobalPlaylist(self, x, y):
    #     self.globalPlayList = []
    #     na = playListDict[playLists[x]][y][0]
    #     va = playListDict[playLists[x]][y][1]
    #     selectedPlaylist = playLists[x]
    #     self.globalPlayList.append((na, va))
    #     iUsedList = []
    #     iUsedList.append(na)
    #
    #     for i in range(len(playListDict[selectedPlaylist])):
    #         inIt = True
    #         for ind in range(len(playListDict[selectedPlaylist]) * len(playListDict[selectedPlaylist])):
    #             songChoice = random.choice(playListDict[selectedPlaylist])
    #             choice = songChoice[0]
    #             if choice in iUsedList:
    #                 pass
    #             else:
    #                 inIt = False
    #                 break
    #         if not inIt:
    #             self.globalPlayList.append((songChoice[0], songChoice[1]))
    #             iUsedList.append(songChoice[0])
    #         else:
    #             pass
    #
    #     self.playlistWasChanged()
    #     self.startSignal()

    def addToGlobalPlaylist(self, x, y):
        na = playListDict[playLists[x]][y][0]
        va = playListDict[playLists[x]][y][1]
        ta = playListDict[playLists[x]][y][2]
        qa = playListDict[playLists[x]][y][3]

        selectedPlaylist = playLists[x]

        self.currentSongInd += 1
        self.current_playlist_start = self.currentSongInd

        try:
            new_playlist = []
            for i in range(self.currentSongInd):
                new_playlist.append(self.globalPlayList[i])

            self.globalPlayList = new_playlist
        except IndexError:
            pass

        self.globalPlayList.append((na, va, ta, qa))
        iUsedList = []
        iUsedList.append(na)

        for i in range(len(playListDict[selectedPlaylist])):
            inIt = True
            for ind in range(len(playListDict[selectedPlaylist]) * len(playListDict[selectedPlaylist])):
                songChoice = random.choice(playListDict[selectedPlaylist])
                choice = songChoice[0]
                if choice in iUsedList:
                    pass
                else:
                    inIt = False
                    break
            if not inIt:
                self.globalPlayList.append((songChoice[0], songChoice[1], songChoice[2], songChoice[3]))
                iUsedList.append(songChoice[0])
            else:
                pass
        self.playlistWasChanged()
        self.startSignal()
        self.updateVolume()

    def setPlayListDict(self):
        if len(playListDict) == 0:
            index = 0
            for name in playLists:
                playListDict[name] = {}
                index += 1
        else:
            pass

    def updatePlayListDict(self):
        self.setPlayListDict()
        valueList = {}
        for playName in playListDict:
            index = 0
            valueList.update({playName: {}})
            if playName in playLists:
                for key in playListDict[playName]:
                    pass
                    valueList[playName].update({index: playListDict[playName][key]})
                    index += 1
            else:
                print('Playlist is not in playLists')

        playListDict.clear()
        playListDict.update(valueList)

        currentDir = os.getcwd()
        myfile = currentDir + r'\playListDict.json'

        # save
        with open(myfile, "w+") as outfile:
            json.dump(playListDict, outfile)

        # playListDict.clear()
        #
        # for valName in valueList:
        #     playListDict.update({valName: valueList[valName]})

        # myfile = r'<filepath>'
        # with open(myfile, "w") as f:
        #     f.seek(0)
        #     f.write(f'playListDict = {playListDict}')
        #     f.truncate()

    def stopSignal(self):
        self.t.stop()

    def checkPlayerState(self):
        try:
            state = self.songPlayingVlc.get_state()

            if (str(state) == 'State.Ended' or str(state) == 'State.Stopped') and self.currentSongInd < len(self.globalPlayList)-1:
                if self.current_loop == 'NONE' or self.current_loop == 'PLAYLIST':
                    self.currentSongInd += 1
                    self.songPlayingVlc = vlc.MediaPlayer(self.globalPlayList[self.currentSongInd][1])
                    self.songPlayingVlc.play()
                    self.currentSongLabel.setText(self.globalPlayList[self.currentSongInd][0])
                    self.pressedPlay()

                elif self.current_loop == 'SONG':
                    if str(state) == 'State.Stopped':
                        self.currentSongInd += 1
                    elif str(state) == 'State.Ended':
                        pass
                if self.vid_on:
                    self.vid_player.stop()
                    self.vid_player = vlc.MediaPlayer(self.globalPlayList[self.currentSongInd][3])
                    self.vid_player.play()

            elif (str(state) == 'State.Ended' or str(state) == 'State.Stopped') and self.currentSongInd == len(self.globalPlayList)-1:
                if self.current_loop == 'NONE':
                    self.currentSongLabel.setText('')
                    self.pressedPause()
                    self.vid_player.stop()
                elif self.current_loop == 'PLAYLIST':
                    self.currentSongInd = self.current_playlist_start
                    self.songPlayingVlc = vlc.MediaPlayer(self.globalPlayList[self.currentSongInd][1])
                    self.songPlayingVlc.play()
                    self.currentSongLabel.setText(self.globalPlayList[self.currentSongInd][0])
                    self.pressedPlay()
                    if self.vid_on:
                        self.vid_player.stop()
                        self.vid_player = vlc.MediaPlayer(self.globalPlayList[self.currentSongInd][3])
                        self.vid_player.play()
                elif self.current_loop == 'SONG':
                    if str(state) == 'State.Stopped':
                        self.currentSongInd += 1
                        self.currentSongLabel.setText('')
                        self.pressedPause()
                    elif str(state) == 'State.Ended':
                        self.songPlayingVlc = vlc.MediaPlayer(self.globalPlayList[self.currentSongInd][1])
                        self.songPlayingVlc.play()
                        self.currentSongLabel.setText(self.globalPlayList[self.currentSongInd][0])
                        self.pressedPlay()
                        if self.vid_on:
                            self.vid_player.stop()
                            self.vid_player = vlc.MediaPlayer(self.globalPlayList[self.currentSongInd][3])
                            self.vid_player.play()

            if str(state) == 'State.Playing':
                self.pressedPlay()

        except:
            pass

    def onPressedSearchBar(self):
        global whatSearch
        self.updatePlayListDict()
        self.activeTable = None
        try:
            for index in range(len(playLists)):
                self.playListDictTable[playLists[index]].clear()
        except:
            pass

        self.hideAllPlaylists()
        self.hideAllMinus()
        self.updatePlayLists()
        self.updateMinus()
        self.updatePlayListTablesMinus()
        self.playlistsTable.show()
        self.createPlaylistButton.show()
        self.updatePlayListTables()
        self.hideAllPlaylists()
        self.hideAllMinus()

        self.butter = True
        whatSearch = self.searchBar.text()
        self.searchBar.setText("")
        self.searchYT(whatSearch)

        self.createPlaylistButton.hide()
        self.createPlaylistGet.hide()
        self.createPlaylistGet.clear()
        self.deletePlaylistButton.hide()
        self.deletePlaylistGet.hide()
        self.deletePlaylistGet.clear()

    def pressedCreatePlaylist(self):
        self.deletePlaylistButton.show()
        self.deletePlaylistGet.clear()
        self.deletePlaylistGet.hide()
        self.createPlaylistButton.hide()
        self.createPlaylistGet.show()

    def addPlaylist(self, name):
        path = os.getcwd()
        myfile = path + r'\playlist.json'
        playLists.append(self.createPlaylistGet.text())
        playListDict.update({self.createPlaylistGet.text(): {}})
        self.updatePlayListDict()
        with open(myfile, "w+") as outfile:
            json.dump(playLists, outfile)
        self.updatePlayLists()
        self.updatePlayListsVisual()
        self.createPlaylistGet.clear()
        self.createPlaylistGet.hide()
        self.createPlaylistButton.show()
        self.updateMinus()
        self.updatePlayListTablesMinus()
        self.updatePlayListTables()
        self.hideAllMinus()

    def addPlaylistLine(self):
        if self.createPlaylistGet.text() not in playLists:
            path = os.getcwd()
            myfile = path + r'\playlist.json'
            playLists.append(self.createPlaylistGet.text())
            playListDict.update({self.createPlaylistGet.text(): {}})
            with open(myfile, "w+") as outfile:
                json.dump(playLists, outfile)
            self.updatePlayListDict()
            self.updatePlayLists()
            self.updatePlayListsVisual()
            self.createPlaylistGet.clear()
            self.createPlaylistGet.hide()
            self.createPlaylistButton.show()
            self.updateMinus()
            self.updatePlayListTablesMinus()
            self.updatePlayListTables()
            self.hideAllMinus()
        else:
            print('Already a playlist')
            self.createPlaylistGet.clear()
            self.createPlaylistGet.hide()
            self.createPlaylistButton.show()

    def updateClickedPlaylists(self):
        self.updatePlayListDict()
        for index in range(len(self.playListDictTable)):
            self.playListButtonDict[index].clicked.connect(lambda state, x=index: self.pressedPlaylist(x))

    def hideAllPlaylists(self):
        for ind in range(len(playLists)):
            self.playListDictTable[playLists[ind]].hide()
        # self.updateClickedPlaylists()


    def hideAllMinus(self):
        # self.updateMinus()
        # self.updatePlayListTablesMinus()
        for ind in range(len(playLists)):
            self.columnDictTable[playLists[ind]].hide()

    def pressedPlaylist(self, index):
        self.updatePlayListDict()
        self.createPlaylistButton.hide()
        self.createPlaylistGet.hide()
        self.deletePlaylistButton.hide()
        self.deletePlaylistGet.hide()
        self.playlistsTable.hide()
        self.hideAllPlaylists()
        self.hideAllMinus()
        self.playListDictTable[playLists[index]].show()
        self.columnDictTable[playLists[index]].show()
        self.activeTable = self.playListDictTable[playLists[index]]

    def updatePlayLists(self):
        self.updatePlayListDict()
        # try:
        #     for index in range(len(playLists)):
        #         self.playListDictTable[playLists[index]].clear()
        # except:
        #     pass
        try:
            self.playListDictTable.clear()
        except:
            pass
        for index in range(len(playLists)):
            self.playListDictTable[playLists[index]] = QtWidgets.QTableWidget(self.centralwidget)
            self.playListDictTable[playLists[index]].setGeometry(QtCore.QRect(50, 100, 345, 361))
            font = QtGui.QFont()
            font.setPointSize(11)
            self.playListDictTable[playLists[index]].setFont(font)
            self.playListDictTable[playLists[index]].setFocusPolicy(QtCore.Qt.NoFocus)
            self.playListDictTable[playLists[index]].setStyleSheet("")
            self.playListDictTable[playLists[index]].setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.playListDictTable[playLists[index]].setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.playListDictTable[playLists[index]].setAutoScroll(False)
            self.playListDictTable[playLists[index]].setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
            self.playListDictTable[playLists[index]].setTabKeyNavigation(False)
            self.playListDictTable[playLists[index]].setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
            self.playListDictTable[playLists[index]].setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
            self.playListDictTable[playLists[index]].setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
            self.playListDictTable[playLists[index]].setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
            self.playListDictTable[playLists[index]].setObjectName("playlistsTable")
            self.playListDictTable[playLists[index]].setColumnCount(1)
            self.playListDictTable[playLists[index]].setStyleSheet("QTableWidget {\n"
                                                                           "     color: white;\n"
                                                                           "     background-color: transparent;\n"
                                                                           "     border: 0px solid red;\n"
                                                                           "    gridline-color: transparent;\n"
                                                                           "}\n"
                                                                           "\n" 
                                                                           "QTableWidget::item {\n"
                                                                           "     padding-top: 20px;\n"
                                                                           "     border-bottom: 1px solid #444444;\n"
                                                                           "     color: white;\n"
                                                                           "}")
            __sortingEnabled = self.playListDictTable[playLists[index]].isSortingEnabled()
            self.playListDictTable[playLists[index]].setSortingEnabled(False)
            self.playListDictTable[playLists[index]].horizontalHeader().setVisible(False)
            self.playListDictTable[playLists[index]].horizontalHeader().setDefaultSectionSize(345)
            self.playListDictTable[playLists[index]].horizontalHeader().setMinimumSectionSize(39)
            self.playListDictTable[playLists[index]].verticalHeader().setVisible(False)
            self.playListDictTable[playLists[index]].verticalHeader().setDefaultSectionSize(75)
            self.playListDictTable[playLists[index]].verticalHeader().setHighlightSections(False)
            self.playListDictTable[playLists[index]].verticalHeader().setMinimumSectionSize(23)
            self.playListDictTable[playLists[index]].hide()
            self.playListDictTable[playLists[index]].clear()
            self.playListDictTable[playLists[index]].verticalScrollBar().valueChanged.connect(lambda state, x=index: self.setOtherScrollBar(x))

    def setOtherScrollBar(self, index):
        value = self.playListDictTable[playLists[index]].verticalScrollBar().value()
        self.columnDictTable[playLists[index]].verticalScrollBar().setValue(value)
        print(value)

    def updateMinus(self):
        self.updatePlayListDict()
        try:
            for index in range(len(playLists)):
                self.columnDictTable[playLists[index]].clear()
        except:
            pass
        for index in range(len(playLists)):
            self.columnDictTable[playLists[index]] = QtWidgets.QTableWidget(self.centralwidget)
            self.columnDictTable[playLists[index]].setGeometry(QtCore.QRect(370, 100, 100, 361))
            font = QtGui.QFont()
            font.setPointSize(11)
            self.columnDictTable[playLists[index]].setFont(font)
            self.columnDictTable[playLists[index]].setFocusPolicy(QtCore.Qt.NoFocus)
            self.columnDictTable[playLists[index]].setStyleSheet("")
            self.columnDictTable[playLists[index]].setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.columnDictTable[playLists[index]].setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.columnDictTable[playLists[index]].setAutoScroll(False)
            self.columnDictTable[playLists[index]].setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
            self.columnDictTable[playLists[index]].setTabKeyNavigation(False)
            self.columnDictTable[playLists[index]].setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
            self.columnDictTable[playLists[index]].setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
            self.columnDictTable[playLists[index]].setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
            self.columnDictTable[playLists[index]].setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
            self.columnDictTable[playLists[index]].setColumnCount(1)
            self.columnDictTable[playLists[index]].setObjectName("minusTable")
            self.columnDictTable[playLists[index]].setStyleSheet("QTableWidget {\n"
                                                                           "     color: white;\n"
                                                                           "     background-color: transparent;\n"
                                                                           "     border: 0px solid red;\n"
                                                                           "    gridline-color: transparent;\n"
                                                                           "}\n"
                                                                           "\n" 
                                                                           "QTableWidget::item {\n"
                                                                           "     padding-top: 20px;\n"
                                                                           "     border-bottom: 0px solid #444444;\n"
                                                                           "     color: white;\n"
                                                                           "}")
            self.columnDictTable[playLists[index]].horizontalHeader().setVisible(False)
            self.columnDictTable[playLists[index]].horizontalHeader().setDefaultSectionSize(320)
            self.columnDictTable[playLists[index]].horizontalHeader().setMinimumSectionSize(39)
            self.columnDictTable[playLists[index]].verticalHeader().setVisible(False)
            self.columnDictTable[playLists[index]].verticalHeader().setDefaultSectionSize(75)
            self.columnDictTable[playLists[index]].verticalHeader().setHighlightSections(False)
            self.columnDictTable[playLists[index]].verticalHeader().setMinimumSectionSize(23)



    def updatePlayListsVisual(self):
        rowCount = len(playListDict)
        self.playlistsTable.setRowCount(rowCount)
        for index in range(rowCount):
            i = int(index)
            self.playListButtonDict[i] = QtWidgets.QPushButton()
            self.playListButtonDict[i].setGeometry(QtCore.QRect(0, 0, 40, 40))
            self.playListButtonDict[i].setStyleSheet("border: 0px solid red;\n"
                                                         "color: white;\n"
                                                         "font-size: 14px;\n"
                                                         "Text-align: left;\n"
                                                         "font: bold;")
            self.playListButtonDict[i].setText(playLists[i])
            self.playListButtonDict[i].setObjectName("playlistTableBtn")
            self.playlistsTable.setCellWidget(index, 0, self.playListButtonDict[i])
            self.playListButtonDict[i].setText(playLists[i])
            self.playListButtonDict[index].clicked.connect(lambda state, x=i: self.pressedPlaylist(x))
        # self.updateClickedPlaylists()

    def iAmTest(self, name):
        print('I am {}'.format(name))

    def updateClickedPlayListButton(self):
        for index in range(len(self.playListButtonDict)):
            whatNum = str(index)
            # print(whatNum)
            self.playListButtonDict[index].clicked.connect(lambda: self.iAmTest(whatNum))

    def createTresDot(self, name, x, y):
        global tresDotPixmap
        nam = name
        val = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.tresDotDict.update({nam: val})
        self.tresDotDict[name].setGeometry(QtCore.QRect(x, y, 30, 30))
        self.tresDotDict[name].setStyleSheet("border: 0px solid white;\n"
                                   "background-color: transparent;")
        self.tresDotDict[name].setText("")
        self.tresDotDict[name].setObjectName(name)

        self.tresDotDict[name].setIcon(QIcon(tresDotPixmap))
        tresDotySize = QSize()
        tresDotySize.setWidth(30)
        tresDotySize.setHeight(30)
        self.tresDotDict[name].setIconSize(tresDotySize)
        n = ''
        v = ''
        if name == 'first':
            n = items_dictionary[0][0]
            v = items_dictionary[0][1]
            t = items_dictionary[0][2]
            q = items_dictionary[0][3]
        elif name == 'second':
            n = items_dictionary[1][0]
            v = items_dictionary[1][1]
            t = items_dictionary[1][2]
            q = items_dictionary[1][3]
        elif name == 'third':
            n = items_dictionary[2][0]
            v = items_dictionary[2][1]
            t = items_dictionary[2][2]
            q = items_dictionary[2][3]
        self.tresDotDict[name].clicked.connect(lambda state, xi=n, yi=v, ti=t, qi=q: self.pressedOpt(xi, yi, ti, qi))

        # temp = name + 'o'
        # self.updateOptDict(temp)
        #
        # self.optDotDict[temp].setGeometry(QtCore.QRect(250, 80, 120, 49))
        # self.optDotDict[temp].setStyleSheet("background-color: transparent;\n"
        #                                     "border: 0px solid white;")
        # self.optDotDict[temp].setFrameShape(QtWidgets.QFrame.StyledPanel)
        # self.optDotDict[temp].setFrameShadow(QtWidgets.QFrame.Raised)
        # self.optDotDict[temp].setObjectName("optionsDropDownFrame")
        #
        # tempop = name + 'op'
        # self.updatePlayDict(tempop)
        #
        # self.playDict[tempop].setGeometry(QtCore.QRect(0, 0, 120, 23))
        # self.playDict[tempop].setStyleSheet("background-color: #666666;")
        # self.playDict[tempop].setObjectName("playlistsButtonAdd")
        #
        # tempol = name + 'ol'
        # self.updateLikedDict(tempol)
        #
        # self.likedDict[tempol].setGeometry(QtCore.QRect(0, 26, 120, 23))
        # self.likedDict[tempol].setStyleSheet("background-color: #666666;")
        # self.likedDict[tempol].setObjectName("likedSongsButtonAdd")

    def updateOptDict(self, name):
        for index in range(len(self.tresDotDict)):
            nam = name
            val = QtWidgets.QFrame(self.scrollAreaWidgetContents)
            self.optDotDict.update({nam: val})

    def updatePlayDict(self, name):
        for index in range(len(self.tresDotDict)):
            nam = name
            val = QtWidgets.QPushButton(self.optionsDropDownFrame)
            self.playDict.update({nam: val})

    def updateLikedDict(self, name):
        for index in range(len(self.tresDotDict)):
            nam = name
            val = QtWidgets.QPushButton(self.optionsDropDownFrame)
            self.likedDict.update({nam: val})

    def dropDownOld(self):
        global arrowPixmap
        t = QTransform()
        t.rotate(180)
        newMap = arrowPixmap.transformed(t)
        arrowPixmap = newMap
        self.dropDownArrowBtn.setIcon(QIcon(arrowPixmap))
        print('done')

    def dropDown(self):
        global arrowPixmap
        global droppedDown
        if not droppedDown:
            t = QTransform()
            t.rotate(90)
            newPixmap = arrowPixmap.transformed(t)
            self.dropFrame()
            droppedDown = True
        else:
            t = QTransform()
            t.rotate(-90)
            newPixmap = arrowPixmap.transformed(t)
            self.pullUpFrame()
            droppedDown = False

        arrowPixmap = newPixmap
        self.dropDownArrowBtn.setIcon(QIcon(arrowPixmap))

    def rotateDropDown(self):
        global arrowPixmap
        arrowPixmap.scaled(512, 512)
        # print(arrowPixmap.size())
        t = QTransform()
        t.rotate(1)
        newPixmap = arrowPixmap.transformed(t)
        arrowPixmap = newPixmap
        self.dropDownArrowBtn.setIcon(QIcon(arrowPixmap))

    def playlistBtnPressed(self):
        self.activeTable = None
        self.hideAllPlaylists()
        self.hideAllMinus()
        self.dropDown()
        self.rotateDropDown()
        self.scrollArea.hide()
        self.updatePlayLists()
        self.updateMinus()
        self.updatePlayListTablesMinus()
        self.playlistsTable.show()
        self.createPlaylistButton.show()
        self.deletePlaylistButton.show()
        self.updatePlayListTables()
        self.hideAllPlaylists()
        self.hideAllMinus()

    def printHelloWorld(self):
        print('Hello World!')

    def dropDownAnim(self):
        anim = QTimeLine(180, self)
        anim.setUpdateInterval(1)
        anim.valueChanged.connect(self.rotateDropDown)
        anim.start()

    def dropFrame(self):
        f = self.dropDownFrame
        x = f.x()
        y = f.y()
        wid = f.width()
        hei = f.height()
        self.anim = QPropertyAnimation(self.dropDownFrame, b'geometry')
        self.anim.setDuration(120)
        self.anim.setStartValue(QRect(x, y, wid, hei))
        y += 49
        self.anim.setEndValue(QRect(x, y, wid, hei))
        self.anim.start()

    def pullUpFrame(self):
        f = self.dropDownFrame
        x = f.x()
        y = f.y()
        wid = f.width()
        hei = f.height()
        self.anim = QPropertyAnimation(self.dropDownFrame, b'geometry')
        self.anim.setDuration(120)
        self.anim.setStartValue(QRect(x, y, wid, hei))
        y -= 49
        self.anim.setEndValue(QRect(x, y, wid, hei))
        self.anim.start()

    def updateVolume(self):
        global volume
        volume = self.volumeSlider.value()
        try:
            self.songPlayingVlc.audio_set_volume(volume)
        except:
            pass
        # print(volume)

    def add_Volume(self):
        global volume
        value = 10
        if 90 >= volume:
            volume += value
        print(volume)
        try:
            self.songPlayingVlc.audio_set_volume(volume)
        except:
            print("Can't change volume")

    def subtract_Volume(self):
        global volume
        value = -10
        if volume >= 10:
            volume += value
        print(volume)
        try:
            self.songPlayingVlc.audio_set_volume(volume)
        except:
            print("Can't change volume")

    def putNameOfSong(self):
        global songPlayingName
        self.currentSongLabel.setText(songPlayingName)

    def firstOptionPressed(self, nothing):
        global volume
        global songPlayingUrl
        global songPlaying
        global songPlayingName
        global items_dictionary
        pUrl = items_dictionary[0][1]
        try:
            currentState = self.songPlayingVlc.get_state()
        except:
            currentState = ''
        if songPlayingUrl == pUrl and currentState == 'State.NothingSpecial':
            print('Same Song')
        else:
            print('Different Song')
            try:
                self.songPlayingVlc.stop()
                self.songPlayingVlc = None
            except:
                print('No Song Playing')
            self.songPlayingVlc = vlc.MediaPlayer(pUrl)
            self.songPlayingVlc.audio_set_volume(volume)
            self.songPlayingVlc.play()
            songPlaying = True
            songPlayingUrl = pUrl
            songPlayingName = items_dictionary[0][0]
            self.putNameOfSong()
            self.pressedPlay()
            self.currentSongLabel.setText(items_dictionary[0][0])

    def secondOptionPressed(self, nothing):
        global volume
        global songPlayingUrl
        global songPlaying
        global songPlayingName
        global items_dictionary
        pUrl = items_dictionary[1][1]
        try:
            currentState = self.songPlayingVlc.get_state()
        except:
            currentState = ''
        if songPlayingUrl == pUrl and currentState == 'State.NothingSpecial':
            print('Same Song')
        else:
            print('Different Song')
            try:
                self.songPlayingVlc.stop()
                self.songPlayingVlc = None
            except:
                print('No Song Playing')
            self.songPlayingVlc = vlc.MediaPlayer(pUrl)
            self.songPlayingVlc.audio_set_volume(volume)
            self.songPlayingVlc.play()
            print(self.songPlayingVlc.get_state())
            self.songPlaying = True
            self.songPlayingUrl = pUrl
            self.songPlayingName = items_dictionary[1][0]
            self.putNameOfSong()
            self.pressedPlay()
            self.currentSongLabel.setText(items_dictionary[1][0])

    def thirdOptionPressed(self, nothing):
        global volume
        global songPlayingUrl
        global songPlaying
        global songPlayingName
        global items_dictionary
        pUrl = items_dictionary[2][1]
        try:
            currentState = self.songPlayingVlc.get_state()
        except:
            currentState = ''
        if songPlayingUrl == pUrl and currentState == 'State.NothingSpecial':
            print('Same Song')
        else:
            print('Different Song')
            try:
                self.songPlayingVlc.stop()
                self.songPlayingVlc = None
            except:
                print('No Song Playing')
            self.songPlayingVlc = vlc.MediaPlayer(pUrl)
            self.songPlayingVlc.audio_set_volume(volume)
            self.songPlayingVlc.play()
            print(self.songPlayingVlc.get_state())
            songPlaying = True
            songPlayingUrl = pUrl
            songPlayingName = items_dictionary[2][0]
            self.putNameOfSong()
            self.pressedPlay()
            self.currentSongLabel.setText(items_dictionary[2][0])

    def pauseDown(self):
        f = self.pauseButton
        x = f.x()
        y = f.y()
        wid = f.width()
        hei = f.height()
        y += 100
        self.pauseButton.setGeometry(QRect(x, y, wid, hei))

    def pauseUp(self):
        f = self.pauseButton
        x = f.x()
        y = f.y()
        wid = f.width()
        hei = f.height()
        y -= 100
        self.pauseButton.setGeometry(QRect(x, y, wid, hei))

    def playDown(self):
        f = self.playButton
        x = f.x()
        y = f.y()
        wid = f.width()
        hei = f.height()
        y += 100
        self.playButton.setGeometry(QRect(x, y, wid, hei))

    def playUp(self):
        f = self.playButton
        x = f.x()
        y = f.y()
        wid = f.width()
        hei = f.height()
        y -= 100
        self.playButton.setGeometry(QRect(x, y, wid, hei))

    def pressedPlay(self):
        playPos = self.playButton.y()
        if playPos == 30:
            try:
                self.songPlayingVlc.pause()
                self.pauseUp()
                self.playDown()
            except:
                print("Nothing to Play/Pause")
        else:
            pass


    def pressedPause(self):
        playPos = self.playButton.y()
        if playPos == 130:
            try:
                self.songPlayingVlc.pause()
                self.pauseDown()
                self.playUp()
                self.ppState = 'PauseUp'
            except:
                print("Nothing to Play/Pause")
        else:
            pass

    def getTitles(self, search):
        queryOne = subprocess.check_output(f'python -m youtube_dl -e --format bestaudio "ytsearch3:{search}" ', universal_newlines=True)
        query = queryOne.splitlines()
        return query

    def getUrls(self, search):
        queryOne = subprocess.check_output(f'python -m youtube_dl --get-url --format bestaudio "ytsearch3:{search}" ',
                                           universal_newlines=True)
        query = queryOne.splitlines()
        return query

    def new_url_aud(self, url):
        try:
            video = pafy.new(url)
            bests = video.audiostreams
            playurl = bests[0].url
            return playurl
        except OSError:
            try:
                video = pafy.new(url)
                bests = video.audiostreams
                playurl = bests[0].url
                return playurl
            except:
                print('Failed to get audio link')


    def new_url_vid(self, url):
        try:
            video = pafy.new(url)
            bests = video.videostreams
            playurl = bests[0].url
            return playurl
        except OSError:
            try:
                video = pafy.new(url)
                bests = video.videostreams
                playurl = bests[0].url
                return playurl
            except:
                print('Failed to get audio link')

    def new_url(self, url):
        print(url)
        try:
            video = pafy.new(url)
            bests = video.audiostreams
            playurl = bests[0].url
            return playurl
        except OSError:
            try:
                video = pafy.new(url)
                bests = video.audiostreams
                playurl = bests[0].url
                return playurl
            except:
                print('Failed to get audio link')

    def get_titles_urls(self, search):

        # Get 3 best results titles and links

        url = 'https://www.youtube.com/results'

        heads = {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
        }

        params = {
            'search_query': search
        }

        with requests.Session() as s:
            r = s.get(url, headers=heads, params=params)

            soup = BeautifulSoup(r.content, 'lxml')

            with open('index.html', 'w+', encoding='utf-8') as f:
                f.write(r.text)

            html = r.text

            ind = html.find('{"responseContext":{"serviceTrackingParams":[{')
            if html.find("scraper_data_begin") == -1:
                end_ind = html.find('window["ytInitialPlayerResponse"] = null;')
            else:
                end_ind = html.find('// scraper_data_end')

            print(html[ind:end_ind])

            dict_raw = html[ind:end_ind]

            to_find = 'title":{"runs":[{"text":'

            titles = []

            urls_youtube = []

            for i in range(len(dict_raw)):
                char = dict_raw[i]
                bad = False
                if char == 't':
                    string = dict_raw[i:i + 24]
                    if string == to_find:
                        new_str = dict_raw[i:]
                        the_ind = new_str.find('accessibility')
                        to_find_two = '{"url":"/watch'
                        if the_ind < 150:
                            title = new_str[25:the_ind - 5]
                            titles.append(title)

                            new_ind = new_str.find(to_find_two)
                            fin_str = new_str[new_ind + 8:]
                            fin_ind = fin_str.find('","webPageType":"')
                            urls_youtube.append('https://www.youtube.com/' + fin_str[:fin_ind])

            print(titles)
            return titles, urls_youtube

    def searchAway(self):
        f = self.searchWarning
        x = f.x()
        y = f.y()
        wid = f.width()
        hei = f.height()
        x += 300
        self.searchWarning.setGeometry(QRect(x, y, wid, hei))

    def searchBack(self):
        f = self.searchWarning
        x = f.x()
        y = f.y()
        wid = f.width()
        hei = f.height()
        x -= 300
        self.searchWarning.setGeometry(QRect(x, y, wid, hei))

    def searchYTFake(self):
        self.searchBack()
        self.searchWarningButton.click()

    def searchYT(self, whatsSearch):
        global items_dictionary
        titlesList, urlList = self.get_titles_urls(whatsSearch)
        # try:
        #     titlesList = self.getTitles(whatToSearch)
        # except:
        #     titlesList = []
        # try:
        #     urlList = self.getUrls(whatToSearch)
        # except:
        #     titlesList = []
        try:
            items_dictionary_d = ((titlesList[0], self.new_url_aud(urlList[0]), urlList[0], self.new_url_vid(urlList[0])), (titlesList[1], self.new_url_aud(urlList[1]), urlList[1], self.new_url_vid(urlList[1])), (titlesList[2], self.new_url_aud(urlList[2]), urlList[2], self.new_url_vid(urlList[2])))
        except:
            items_dictionary_d = (('', '', ''), ('', '', ''), ('', '', ''))
        items_dictionary = items_dictionary_d

        # Set first Option items_dictionary[0][0]
        self.firstOption.setText(items_dictionary[0][0])

        # Set second Option items_dictionary[1][0]
        self.secondOption.setText(items_dictionary[1][0])

        # Set third Option items_dictionary[2][0]
        self.thirdOption.setText(items_dictionary[2][0])

        self.createTresDot('first', 340, 50)
        self.createTresDot('second', 340, 165)
        self.createTresDot('third', 340, 280)

        self.scrollArea.show()
        self.playlistsTable.hide()
        self.createPlaylistButton.hide()
        self.deletePlaylistButton.hide()
        self.hideAllPlaylists()

        self.tresDotDict['first'].show()
        self.tresDotDict['second'].show()
        self.tresDotDict['third'].show()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    with open('style.css', 'r') as style:
        app.setStyleSheet(style.read())
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
