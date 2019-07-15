def web_url(url):
    return url.startswith('https://') or url.startswith('http://')

def get_length(milliseconds, letter: bool = False):
    if not milliseconds:
        return 'LIVESTREAM'
        
    h, _ = divmod(milliseconds / 1000, 3600); m, s = divmod(_, 60)
    return '%02dh %02dm %02ds' % (h, m, s) if letter else '%02d:%02d:%02d' % (h, m, s)