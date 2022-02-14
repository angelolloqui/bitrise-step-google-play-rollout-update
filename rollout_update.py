
import copy
import sys
import httplib2
from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client.client import AccessTokenRefreshError

TRACK = ('production')

# To run: rollout_update package_name json_credentials_path
def main():
  PACKAGE_NAME = sys.argv[1]
  credentials = ServiceAccountCredentials.from_json_keyfile_name(
    sys.argv[2],
    scopes='https://www.googleapis.com/auth/androidpublisher')

  http = httplib2.Http()
  http = credentials.authorize(http)

  service = build('androidpublisher', 'v3', http=http)

  try:
    edit_request = service.edits().insert(body={}, packageName=PACKAGE_NAME)
    result = edit_request.execute()
    edit_id = result['id']

    track_result = service.edits().tracks().get(editId=edit_id, packageName=PACKAGE_NAME, track=TRACK).execute()
    old_result = copy.deepcopy(track_result)

    print("Current status: ", track_result)
    for release in track_result['releases']:
        if 'userFraction' in release:
            rolloutPercentage = release['userFraction']
            if rolloutPercentage == 0:
                print('Release not rolled out yet')
                continue
            elif rolloutPercentage < 0.01:
                release['userFraction'] = 0.01                         
            elif rolloutPercentage < 0.02:
                release['userFraction'] = 0.02                         
            elif rolloutPercentage < 0.05:
                release['userFraction'] = 0.05
            elif rolloutPercentage < 0.1:
                release['userFraction'] = 0.1
            elif rolloutPercentage < 0.2:
                release['userFraction'] = 0.2
            elif rolloutPercentage < 0.5:
                release['userFraction'] = 0.5
            elif rolloutPercentage < 1.0:
                del release['userFraction']
                release['status'] = 'completed'
            else:
                print('Release already fully rolled out')
                continue        
    if old_result != track_result:
        completed_releases = list(filter(lambda release: release['status'] == "completed", track_result['releases']))
        if len(completed_releases) == 2:
            track_result['releases'].remove(completed_releases[1])

        print("Updating status: ", track_result)
        service.edits().tracks().update(
                    editId=edit_id,
                    track=TRACK,
                    packageName=PACKAGE_NAME,
                    body=track_result).execute()
        commit_request = service.edits().commit(editId=edit_id, packageName=PACKAGE_NAME).execute()
        print('✅ Edit ', commit_request['id'], ' has been committed')    
    else:
        print('✅ No rollout update needed, already in 100%')


  except AccessTokenRefreshError:
      raise SystemExit('The credentials have been revoked or expired, please re-run the application to re-authorize')

if __name__ == '__main__':
  main()