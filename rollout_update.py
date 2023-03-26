
import copy
import sys
import httplib2
from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client.client import AccessTokenRefreshError

# To run: rollout_update package_name json_credentials_path track force_user_fraction
def main():
  PACKAGE_NAME = sys.argv[1]
  TRACK = sys.argv[3]
  FORCE_USER_FRACTION = float(sys.argv[4] or "0")

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
            if FORCE_USER_FRACTION > 0:
                rolloutPercentage = FORCE_USER_FRACTION
                print('Forcing rollout to', rolloutPercentage)
            else:                
                if rolloutPercentage <= 0.0001:
                    print('Release not rolled out yet')
                    continue
                elif rolloutPercentage < 0.02:
                    rolloutPercentage = 0.02                         
                elif rolloutPercentage < 0.05:
                    rolloutPercentage = 0.05
                elif rolloutPercentage < 0.1:
                    rolloutPercentage = 0.1
                elif rolloutPercentage < 0.2:
                    rolloutPercentage = 0.2
                elif rolloutPercentage < 0.5:
                    rolloutPercentage = 0.5
                elif rolloutPercentage < 1.0:
                    rolloutPercentage = 1.0
                else:
                    print('Release already fully rolled out')
                    continue                
            if rolloutPercentage < 1:
                print('Updating rollout to', rolloutPercentage)
                release['userFraction'] = rolloutPercentage
            else:
                print('Marking rollout completed', rolloutPercentage)
                del release['userFraction']
                release['status'] = 'completed'            

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
        print('✅ No rollout update needed')


  except AccessTokenRefreshError:
      raise SystemExit('The credentials have been revoked or expired, please re-run the application to re-authorize')

if __name__ == '__main__':
  main()
