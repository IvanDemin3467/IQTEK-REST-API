from requests import post, get, patch, delete

if __name__ == '__main__':

    # Successfull
    print(get('http://localhost:80/users').json())  # show all
    print(get('http://localhost:80/user/2').json())   # show one existing
    print(post('http://localhost:80/user/3?title=Mikhail%20Vasilevich%20Lomonosov'))  # add new non existing
    print(get('http://localhost:80/users').json())  # show all
    print(patch('http://localhost:80/user/3?title=Just%20Lomonosov'))  # update existing
    print(get('http://localhost:80/users').json())  # show all
    print(delete('http://localhost:80/user/3'))  # delete existing
    print(get('http://localhost:80/users').json())  # show all
    # Rejected
    print(get('http://localhost:80/user/3').text)   # show one non existing
    print(post('http://localhost:80/user/2?title=Mikhail%20Vasilevich%20Lomonosov').text)   # add at the place of existing
    print(patch('http://localhost:80/user/3?title=Just%20Lomonosov').text)  # modify non existing
    print(delete('http://localhost:80/user/3').text)  # delete non existing
    delete('http://localhost:80/user/2')  # delete all
    delete('http://localhost:80/user/1')
    print(get('http://localhost:80/users').text)  # show empty DB
