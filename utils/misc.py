def web_url(url):
    return url.startswith('https://') or url.startswith('http://')


def get_length(milliseconds, letter: bool = False):
    if not milliseconds:
        return 'LIVESTREAM'

    m, s = divmod(milliseconds / 1000, 60); h, m = divmod(m, 60)
    if not letter:
        return '%02d:%02d:%02d' % (h, m, s)

    d, h = divmod(h, 24)
    output = '%1ds' % s

    if m >= 1: output = '%1dm ' % m + output
    if h >= 1: output = '%1dh ' % h + output
    if d >= 1: output = '%1dd ' % d + output

    return output
