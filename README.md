# subversion-slack-bot

## Install steps
<ol type="1">
  <li>Clone repository</li>
  <li>Add Incoming WebHooks to your team in Slack (https://<b>teamdomain</b>.slack.com/apps/build/custom-integration - replace <b>teamdomain</b> with your team name in Slack)</li>
  <li>Make changes in https://github.com/dimadl/subversion-slack-bot/blob/master/subversion.py
    <ul>
      <li>Provide usernmame for SVN (variable <b>username</b>) </li>
      <li>Provide password for SVN (variable <b>password</b>)</li>
      <li>Provide path to the branch you want to track (variable <b>barnch_path</b>)</li>
      <li>Provide WebHook URL (variable <b>domain_url</b>)
      <li>Provide full local path to the repository (variable <b>pwd</b>)<br>
         <i>e.g <b>Linux:</b> pwd = '/home/user/subversion-slack-bot'</i>
      </li>
    </ul>
  </li>
  <li>
    <p>Make changes in https://github.com/dimadl/subversion-slack-bot/blob/master/run.sh
    <p>Provide a full path to the python script (e.d python /home/user/subversion-slack-bot/subversion.py)
  </li>
  <li>
    Set up cron which will call run.sh script. 
    <p><i>e.g. */5 * * * * bash /home/user/subversion-slack-bot/run.sh</i> - run.sh will be called every five minutes
  </li>
  
</ol>
  
