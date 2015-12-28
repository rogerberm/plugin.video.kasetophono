import sys
import re
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urlparse
import urllib
import CommonFunctions
import random

common = CommonFunctions
common.plugin = 'kasetophono-1.0'

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
xbmcplugin.setContent(addon_handle, 'musicvideos')
args = urlparse.parse_qs(sys.argv[2][1:])

content_type = args.get('content_type', [None])[0]

addon = xbmcaddon.Addon()
addon_fanart = addon.getAddonInfo('fanart')


def loadItems():
	url = 'plugin://plugin.video.youtube/?path=/root/video&action=play_all&playlist=PLSRDGXudTSm_aadb8ewwyg_F_G0peX2qL'
	li2 = xbmcgui.ListItem('content_type=' + content_type, iconImage='DefaultVideo.png')
	li3 = xbmcgui.ListItem('My first video!', iconImage='DefaultVideo.png')
	xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li2)

	xbmcplugin.endOfDirectory(addon_handle)

def build_url(query):
	return base_url + '?' + urllib.urlencode(query)

def getHtml(url):
	return urllib.urlopen(url).read()

def findStuff():
	htmlcontent = getHtml('http://www.kasetophono.com');
	thestuff = common.parseDOM(htmlcontent, 'ul', attrs = {'id': 'mbt-menu'})
	print repr(thestuff)

def findDefaultTopics():
	topic_regex = [u'http://www.kasetophono.com/.*/xena.html', 'http://www.kasetophono.com/.*/greek.html', 'http://www.kasetophono.com/.*/mood.html']
	topic_ids = ['genres', 'greek', 'mood']
	topic_regex = map(re.compile, topic_regex)
	htmlcontent = getHtml('http://www.kasetophono.com')
	subhtml = common.parseDOM(htmlcontent, 'ul', attrs = {'id': 'mbt-menu'})
	global_categories = common.parseDOM(subhtml, 'li')
	result = {}
	for global_category in global_categories:
		global_category_title = common.parseDOM(global_category, 'a')
		global_category_url = common.parseDOM(global_category, 'a', ret = 'href')
		if len(global_category_url)>0:
			for (rx, topic) in zip(topic_regex, topic_ids):
				if rx.match(global_category_url[0]):
					result[topic] = zip(global_category_url, global_category_title)
					#print zip(global_category_url, global_category_title) 
				else:
					#print global_category_url[0]
					pass
	return result
	#print len(global_categories)
	#print repr(subhtml)

def loadRootItems():
	genres_item = xbmcgui.ListItem('Genres', iconImage='DefaultAutio.png')
	greek_item = xbmcgui.ListItem('Greek', iconImage='DefaultFolder.png')
	mood_item = xbmcgui.ListItem('Moods', iconImage='DefaultFolder.png')
	all_item = xbmcgui.ListItem('All', iconImage='DefaultFolder.png')
	roulette_item = xbmcgui.ListItem('Roulette!', iconImage='DefaultFolder.png')

	genres_url = build_url({'mode':'folder', 'foldername':'genres'})
	greek_url = build_url({'mode':'folder', 'foldername':'greek'})
	mood_url = build_url({'mode':'folder', 'foldername':'mood'})
	all_url = build_url({'mode':'all'})
	roulette_url = build_url({'mode':'random'})

	roulette_first = addon.getSetting('roulettefirst') == 'true'
	roulette_item.setProperty('IsPlayable', 'true')
	if roulette_first:
		directory_items = [roulette_item, genres_item, greek_item, mood_item, all_item]
		directory_urls = [roulette_url, genres_url, greek_url, mood_url, all_url]
	else:
		directory_items = [genres_item, greek_item, mood_item, all_item, roulette_item]
		directory_urls = [genres_url, greek_url, mood_url, all_url, roulette_url]
	for (directory_item, directory_url) in zip(directory_items, directory_urls):
		directory_item.setArt({'fanart':addon_fanart})
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=directory_url, listitem=directory_item, isFolder=not directory_item.getProperty('IsPlayable') == 'true')
	xbmcplugin.endOfDirectory(addon_handle)

def loadRandom():
	playlist = getRandomPlaylist()
	playlist_id = playlist['youtube_url']
	playlist_id = playlist_id[playlist_id.find('=')+1:]
	order = int(addon.getSetting('order'))
	if order<3:
		url = 'plugin://plugin.video.youtube/play/?playlist_id={0}&order={1}'.format(playlist_id,['default', 'reverse', 'shuffle'][order-1])
	else:
		url = 'plugin://plugin.video.youtube/play/?playlist_id={0}'.format(playlist_id)
	play_item = xbmcgui.ListItem(path=url)
	xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)
	print 'should play random now'
	return


def loadFolder(folderName):
	default_topics = findDefaultTopics()[folderName]
	
	for (topic_url, topic_name) in default_topics:
		item = xbmcgui.ListItem(topic_name, iconImage='DefaultAudio.png')
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=topic_url, listitem=item)

	placeholder_item = xbmcgui.ListItem('Placeholder for ' + folderName, iconImage='DefaultAudio')
	xbmcplugin.addDirectoryItem(handle=addon_handle, url=base_url, listitem=placeholder_item)
	xbmcplugin.endOfDirectory(addon_handle)


def getEntryInfo(entry):
	entry_info = {}
	entry_info['title'] = common.parseDOM(entry, 'title')[0]
	entry_info['thumbnail'] = common.parseDOM(entry, 'media:thumbnail', ret='url')[0]
	entry_info['summary'] = common.parseDOM(entry, 'summary')
	entry_info['categories'] = common.parseDOM(entry, 'category', ret='term')[0]
	entry_info['isBlog'] = any([category=='blog' for category in entry_info['categories']])
	entry_info['url'] = common.parseDOM(entry, 'link', attrs={'rel': 'self'}, ret='href')
	content = common.parseDOM(entry, 'content')
	content = content[0].replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot', '"')
	entry_info['youtube_url'] = common.parseDOM(content, 'iframe', ret='src')[0]
	return entry_info


def getNumPlaylists():
	htmlcontent = getHtml('http://www.kasetophono.com/feeds/posts/summary/-/Playlist?max-results=0')
	num_playlists = common.parseDOM(htmlcontent, 'openSearch:totalResults')
	num_playlists = int(num_playlists[0])
	return num_playlists


def getRandomPlaylist():
	num_playlists = getNumPlaylists()
	selected_playlist = random.randint(1,num_playlists)
	htmlcontent = getHtml('http://www.kasetophono.com/feeds/posts/default/-/Playlist?start-index={0}&max-results=1'.format(selected_playlist))
	playlist = common.parseDOM(htmlcontent, 'entry')[0]
	entry_info = getEntryInfo(playlist)
	return entry_info			


def loadAll():
	#htmlcontent = getHtml('http://www.kasetophono.com/feeds/posts/summary/-/popular?max-results=50')
	htmlcontent = getHtml('http://www.kasetophono.com/feeds/posts/default?max-results=11300')
	entries= common.parseDOM(htmlcontent.replace(': ', ':'), 'entry')
	for entry in entries:
		title = common.parseDOM(entry, 'title')
		thumbnail = common.parseDOM(entry, 'media:thumbnail', ret='url')
		summary = common.parseDOM(entry, 'summary')
		categories = common.parseDOM(entry, 'category', ret='term')
		isBlog = any([category=='blog' for category in categories])
		print title
		if len(categories)>0:
			if not isBlog:
				url = common.parseDOM(entry, 'link', attrs={'rel': 'self'}, ret='href')
				item = xbmcgui.ListItem(title[0].replace('&#39;', '\''))
				item.setArt({'thumb': thumbnail[0]})
				item.setProperty('IsPlayable', 'true')
				if len(summary)>0:
					item.setInfo('video', {'plot': urllib.unquote_plus(summary[0]), 'plotoutline': summary[0]})
				xbmcplugin.addDirectoryItem(handle=addon_handle, url=build_url({'mode':'playlist', 'url':url[0]}), listitem=item, isFolder=False)
		else:
			print repr(title[0]) + ' doesnt have categories!'
	xbmcplugin.endOfDirectory(addon_handle)

def loadPlaylist(playlist_url):
	htmlcontent = getHtml(playlist_url)
	content = common.parseDOM(htmlcontent, 'content')
	content = content[0].replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot', '"')
	youtube_ref = common.parseDOM(content, 'iframe', ret='src')
	print(len(youtube_ref))
	youtube_ref = youtube_ref[0]
	#dialog = xbmcgui.Dialog()
	#dialog.ok('testing', content)
	print 'Loading playlist ' + playlist_url
	print 'Loading youtube playlist ' + youtube_ref
	playlist_id = youtube_ref[youtube_ref.find('=')+1:]
	order = int(addon.getSetting('order'))
	print order
	if order<3:
		url = 'plugin://plugin.video.youtube/play/?playlist_id={0}&order={1}'.format(playlist_id,['default', 'reverse', 'shuffle'][order-1])
	else:
		url = 'plugin://plugin.video.youtube/play/?playlist_id={0}'.format(playlist_id)
	play_item = xbmcgui.ListItem(path=url)
	xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)
	#xbmc.executebuiltin('RunPlugin(%s)' % url)

mode = args.get('mode', [None])[0]

if mode is None:
	loadRootItems()
elif mode == 'random':
	loadRandom()
elif mode == 'folder':
	folderName = args.get('foldername', [None])[0]
	loadFolder(folderName)
elif mode == 'playlist':
	playlist_url = args.get('url', [None])[0]
	loadPlaylist(playlist_url)
elif mode == 'all':
	loadAll()
else:
	print mode

