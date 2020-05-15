#!/usr/bin/perl
our $VERSION = "0.0.5"; # Time-stamp: <2020-05-15T05:30:28Z>";

##
## Author:
##
##   JRF ( http://jrf.cocolog-nifty.com/statuses/ )
##
## Repository:
##
##   https://github.com/JRF-2018/memo_cgi
##
## License:
##
##   Public Domain
##   (because this program is as small as a mathematical formula).
##

use strict;
use warnings;
use utf8; # Japanese

use CGI;
use Encode;
use Fcntl qw(:DEFAULT :flock :seek);

our $TEXT_FILE = "memo.txt";
#our $PASSWORD = "test";
our $TEXT_MAX = 1024 * 1024;
our $CGI = CGI->new;
binmode(STDOUT, ":utf8");

$SIG{__DIE__} = sub {
  my $message = shift;
  print $CGI->header(-type => 'text/html',
		     -charset => 'utf-8',
		     -status => '500 Internal Server Error');
  print <<"EOT";
<\!DOCTYPE html>
<html>
<head>
<title>ERROR</title>
</head>
<body>
<p>Die: $message</p>
</body>
</html>
EOT
  exit(1);
};

sub escape_html {
  my ($s) = @_;
  $s =~ s/\&/\&amp\;/sg;
  $s =~ s/</\&lt\;/sg;
  $s =~ s/>/\&gt\;/sg;
#  $s =~ s/\'/\&apos\;/sg;
  $s =~ s/\"/\&quot\;/sg;
  return $s;
}

sub main {
  my $txt = $CGI->param('txt');
  if (defined $txt) {
    # my $pass = $CGI->param('pass');
    # die "Wrong password." if ! defined $pass || $pass ne $PASSWORD;
    $txt = Encode::decode('UTF-8', $txt);
    if (length($txt) > $TEXT_MAX) {
      $txt = substr($txt, 0, $TEXT_MAX);
    }
    sysopen(my $fh, $TEXT_FILE, O_RDWR | O_CREAT)
      or die "Cannot open $TEXT_FILE: $!";
    flock($fh, LOCK_EX)
      or die "Cannot lock $TEXT_FILE: $!";
    seek($fh, 0, SEEK_SET)
      or die "Cannot seek $TEXT_FILE: $!";
    binmode($fh);
    my $btxt = Encode::encode('UTF-8', $txt);
    print $fh $btxt
      or die "Cannot Write $TEXT_FILE: $!";
    truncate($fh, length($btxt));
    flock($fh, LOCK_UN);
    close($fh);
  } else {
    sysopen(my $fh, $TEXT_FILE, O_RDWR | O_CREAT)
      or die "Cannot open $TEXT_FILE: $!";
    flock($fh, LOCK_SH)
      or die "Cannot lock $TEXT_FILE: $!";
    binmode($fh);
    my $btxt = join("", <$fh>);
    flock($fh, LOCK_UN);
    close($fh);
    $txt = Encode::decode('UTF-8', $btxt);
  }
  print $CGI->header(-type => 'text/html',
		     -charset => 'utf-8');
  $txt = escape_html($txt);
  print <<"EOT";
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta name="robots" content="noindex,nofollow" />
<meta name="viewport" content="width=device-width,initial-scale=1" />

<title>Memo</title>
<!-- memo.cgi version $VERSION -->
<style type="text/css">
</style>
<script type="text/javascript">
<!--
function resizeTextareaIfSmartphone() {
  if (window.matchMedia
      && window.matchMedia('(max-device-width: 640px)').matches) {
    var txt = document.getElementById("txt");
    txt.style.width = "90%";
    txt.style.height = Math.floor(window.innerHeight *  0.9) + "px";
  }
}
-->
</script>
</head>
<body onLoad="resizeTextareaIfSmartphone()">
<form action="memo.cgi" method="post">
<textarea id="txt" name="txt" rows="30" cols="80">$txt</textarea>
<br/>
<!--
Pass: <input type="password" name="pass" />
-->
<input type="submit" value="Submit" />
</form>
</body>
</html>
EOT
}

main();
exit(0);
