def humanize_value(number, value):
    """
    "Humanizes" a name, Ex: 1 time, 2 times
    """
    if number == 1:
        return f"{number} {value}"
    else:
        return f"{number} {value}s"


def humanize_list(list):
    """
    Makes a list easier to read
    """
    if not list:
        return list
    if len(list) == 1:
        return list[0]
    if len(list) == 2:
        return " and ".join(list)
    return f"{', '.join(str(item) for item in list[:-1])} and {list[-1]}"
