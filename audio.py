#! /usr/bin/env python
# -*- coding: utf8 -*-
# Preliminary audio engine (Rhythmbox)
import globals as iglobals

from twisted.web.resource import Resource

if (iglobals.audio):
	import dbus	
	bus = dbus.SessionBus()
	rbshellobj = bus.get_object('org.gnome.Rhythmbox', '/org/gnome/Rhythmbox/Shell')
	rbshell = dbus.Interface(rbshellobj, 'org.gnome.Rhythmbox.Shell')
	rbplayerobj = bus.get_object('org.gnome.Rhythmbox', '/org/gnome/Rhythmbox/Player')
	rbplayer = dbus.Interface(rbplayerobj, 'org.gnome.Rhythmbox.Player')
	rburi = rbplayer.getPlayingUri()

class AudioResource(Resource):
	""" Get the current playing song. """
	def getAudiodata(self):
		""" This class should return a string with what you
		want the Now Listening: tag to display. """
		self.playing = rbplayer.getPlayingUri().replace('%20', ' ').replace('file://', '').replace('%F1', 'n').replace('%E9', 'e').replace('%C3%AD', 'i').replace('%C3%A9', 'e')
		#self.playing = urllib.unquote(rbplayer.getPlayingUri())
		return self.playing
	
	def render_GET(self, request):
		""" Handle GET requests for audio.html. """
		request.setHeader("Content-type", "text/html; charset=UTF-8'")
		self.getAudiodata()
		#igui.talk('updateSongStatus', str(self.playingi), None)
		return "<strong>Escuchando: %s.</strong>" % (str(self.playing))

