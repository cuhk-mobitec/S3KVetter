from facebook import get_user_from_cookie, GraphAPI,auth_url
#from symbolic.args import *


# Facebook app details
FB_APP_ID = '156258847901639'
FB_APP_NAME = 'LoginSample'
FB_APP_SECRET = '3ea39e503951c8db93ef73d68fd6f22a'

#perms = ['manage_pages','publish_pages']
@symbolic(user=0)
def test(user):
    graph = GraphAPI(version='2.2')
    # generate the login url
    perms=['manage_pages']
    canvas_url = 'https://domain.com/that-handles-auth-response/'
    fb_login_url = auth_url(FB_APP_ID, canvas_url, perms)   
    
    print(fb_login_url)
    cookies={"fbm_15625884790163":"base_domain=.yangronghai.github.io","fbsr_156258847901639":"-rRNSU9o80WdyH3nvUYiFNOYdA1tPEJo4Jp_eE1tqeY.eyJhbGdvcml0aG0iOiJITUFDLVNIQTI1NiIsImNvZGUiOiJBUUM3Ukl6UHoyNTZaWGZzdHRSMzBPYXFnc1h3V2RQeVBJN3R4d0loaEJrX1FLZUtoSG9xMTEyTjlfZFBjZldTWEloV3JQWUR0SXZVQXJ0UzA4Q1JEMm53ZXQ2UGttR2J6NkNBSzA0WGpWRVBjS015dmhiUEdPYU9UUk1Cdk5GQlhDTVlGN3g2a3dBbFZQV1U5Mi1IbWRMT2tjSGVzTjNjVmFSV3B4VzlMeXA3SW9jM0Z0NjBtQlZ4NlJ5bzJwcW9vVkQ1MFdFY3BIVGc0R1MzcEc5bDIybUZ5cllEVVZKRGVxRGw4VTh0dDJjcW9oSWV5eDJENzlmSktGZmtRajEzdGh1N21vV05ZOEdWenlyNUxSNWJmWmZfRDdaMlJqSzE2eFFFYV94LXE0NVB3WVE2VlVMdHdMeXowaHJFRTVFQWM0M3NLYmZpNVhnZGVWcG1kX0lNMTd1TSIsImlzc3VlZF9hdCI6MTQ4OTM4Nzk1MCwidXNlcl9pZCI6IjE1MDAwNzE3NzY5NTMyMzEifQ"}
    # use the response to authenticate the user
    result = get_user_from_cookie(cookies=cookies, app_id=FB_APP_ID,
                                  app_secret=FB_APP_SECRET)

    # If there is no result, we assume the user is not logged in.
    if result:
        # Check to see if this user is already in our database.
        #user = User.query.filter(User.id == result['uid']).first()

        if not user:
            # Not an existing user so get info
            graph = GraphAPI(result['access_token'])
            profile = graph.get_object('me')
            if 'link' not in profile:
                profile['link'] = ""

            # Create the user and insert it into the database
            user = User(id=str(profile['id']), name=profile['name'],
                        profile_url=profile['link'],
                        access_token=result['access_token'])
            #db.session.add(user)
        elif user.access_token != result['access_token']:
            # If an existing user, update the access token
            user.access_token = result['access_token']

        # Add the user to the current session
        #session['user'] = dict(name=user.name, profile_url=user.profile_url,
        #    id=user.id, access_token=user.access_token)

    # Commit changes to the database and set the user as a global g.user
    # db.session.commit()
    #g.user = session.get('user', None)
    return user
if __name__=="__main__":
    test(0)
