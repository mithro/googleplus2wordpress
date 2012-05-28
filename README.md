
Import data from Google+ to Wordpress
-------------------------------------------------------------------------------

Will eventually sync both posts and comments on the posts.

Uses the Google+ Public API, so can only sync public posts. Uses it via the
google-api-python-client python module.

Uses the Wordpress XMLRPC API, so that needs to be enabled. Uses it via the 
python-wordpress-xmlrpc python module.

html2text and nltk are used for generating a much nicer title then G+ produces.
(By getting the first sentance.)

oEmbed is used to get some nice extra information about the stuff we are trying
to embed, because G+ is really crappy at passing useful info. (We also use my
custom Picasa Web oEmbed endpoint to do video embedding).

We produce a bunch of different post types to allow styling different;

 * Standard Text Post
 * Single Photo/Video post
 * Gallery Post (collection of Photo/Videoes) 
    * http://highslide.com
 * Website share

There is also a "reshare" post which is basically one of the above post types
wrapped in a reshare block tell who it came from.


Set Up
-------------------------------------------------------------------------------
Install requirements in requirements.txt

	# sudo pip install -r requirements.txt

Create a config.py with your Embedly key;

	# cat > config.py <<EOF
	EMBEDLY_KEY = 'XXXXXXXXXXXXXXXXXXXXXXXXXXX'
	EOF

Create a client_secrets.json with your G+ API key details;

	# cat > client_secrets.json <<EOF
	{
	  "web": {
	    "client_id": "XXXXXXXXXXXXXXXXXXXXXXXXXX.apps.googleusercontent.com",
	    "client_secret": "XXXXXXXXXXXXXXXXXXXXXXXX",
	    "redirect_uris": [],
	    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
	    "token_uri": "https://accounts.google.com/o/oauth2/token"
	  }
	}
	EOF

Run the command
# python plus.py 


Wordpress Side
-------------------------------------------------------------------------------
*** Warning PHP code! ***

Stores the G+ ids in the Wordpress Meta information - 

	'meta_query' => array(
		array(
			'key' => 'google_plus_(activity|comment)_id',
			'value' => XXXX,
		),

We use the following Wordpress filter, to support showing Google+ photos in the
comments; this basically stores the URL in the meta data under 'google_plus_comment_avatar'.


	function get_avatar_google($avatar, $id_or_email, $size, $default, $alt) {

	    if (isset($id_or_email->comment_ID)) {
		$plus_avatar = get_comment_meta($id_or_email->comment_ID, 'google_plus_comment_avatar', true);
		$matches = array();
		if (preg_match('/(https:\/\/.*\.googleusercontent\.com.*)\?sz=\d+/', $plus_avatar, $matches)) {
		    return "<img alt='{$safe_alt}' src='{$matches[1]}?sz=$size' class='avatar avatar-{$size} photo' height='{$size}' width='{$size}' />";
		}
	    }
	    return $avatar;
	}

	add_filter( 'get_avatar', 'get_avatar_google', 1, 5);
