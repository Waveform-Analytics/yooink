# API access

To get OOI API access, you'll need a username and token.

1. Create a user account on ooinet.oceanobservatories.org (you can also use an existing CILogin or Google account.
2. Log in
3. Navigate to the drop down menu screen in the top-right corner menu
4. Click on the “User Profile” element of the drop down
5. Scroll to the bottom to see your API Username and API Token

## API token security

You'll notice that down below you need to provide an API key and token. 
Those definitely shouldn't be hard coded into a file that lives on a public 
(or really even private) repository. An easy way to handle that is to 
store your API key and token as local environment variables and then use the
 os library to access the contents of the environment variable.
 
To save that environment variable using macOS or Linux terminal, use:

`export OOI_USER=abc123` 

On Windows, you'd use:

`setx OOI_TOKEN "abc123"`

You can access those environment variables in Python using:

```python
import os

api_username = os.getenv('OOI_USER')
```

**Other options**

- Save environment variables more permanently on your local computer. We won't go into detail here but you can find lots of simple instructions if you do a quick google search.
- Hard-code those values right into the script. Just be careful not to upload!
