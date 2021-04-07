def check_if_tag_exists(list_of_tags, new_tag):
    exists = False
    for tag in list_of_tags:
        if tag['tag'] == new_tag['tag'] or tag['localisation'] == new_tag['localisation']:
            exists = True
            break
    return exists