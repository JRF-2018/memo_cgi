#!/usr/bin/perl
our $VERSION = "0.0.11"; # Time-stamp: <2020-05-16T10:21:11Z>";

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
use Encode qw(encode decode);
use Fcntl qw(:DEFAULT :flock :seek);

our $TEXT_FILE_1 = "memo1.txt";
our $TEXT_FILE_2 = "memo2.txt";
#our $PASSWORD = "test";
our $TEXT_MAX = int(3000000 / 6); # 6 == safe utf8 max bytes.
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

sub txt_read {
  my ($file) = @_;
  sysopen(my $fh, $file, O_RDWR | O_CREAT)
    or die "Cannot open $file: $!";
  flock($fh, LOCK_SH)
    or die "Cannot lock $file: $!";
  binmode($fh);
  my $btxt = join("", <$fh>);
  flock($fh, LOCK_UN);
  close($fh);
  return decode('UTF-8', $btxt);
}

sub txt_write {
  my ($file, $txt) = @_;
  sysopen(my $fh, $file, O_RDWR | O_CREAT)
    or die "Cannot open $file: $!";
  flock($fh, LOCK_EX)
    or die "Cannot lock $file: $!";
  seek($fh, 0, SEEK_SET)
    or die "Cannot seek $file: $!";
  binmode($fh);
  my $btxt = encode('UTF-8', $txt);
  print $fh $btxt
    or die "Cannot Write $file: $!";
  truncate($fh, length($btxt));
  flock($fh, LOCK_UN);
  close($fh);
}

sub main {
  my $cmd = $CGI->param('cmd') || 'reload';
  my $flag1 = $CGI->param('flag1') || 0;
  my $flag2 = $CGI->param('flag2') || 0;
  if ($cmd eq 'reload') {
    $flag1 = 0;
    $flag2 = 0;
  }
  my $txt1;
  my $txt2;
  if ($flag1) {
    # my $pass = $CGI->param('pass');
    # die "Wrong password." if ! defined $pass || $pass ne $PASSWORD;
    $txt1 = $CGI->param('txt1') || "";
    $txt1 = decode('UTF-8', $txt1);
    if (length($txt1) > $TEXT_MAX) {
      $txt1 = substr($txt1, 0, $TEXT_MAX);
    }
    txt_write($TEXT_FILE_1, $txt1);
  } else {
    $txt1 = txt_read($TEXT_FILE_1);
  }
  if ($flag2) {
    # my $pass = $CGI->param('pass');
    # die "Wrong password." if ! defined $pass || $pass ne $PASSWORD;
    $txt2 = $CGI->param('txt2') || "";
    $txt2 = decode('UTF-8', $txt2);
    if (length($txt2) > $TEXT_MAX) {
      $txt2 = substr($txt2, 0, $TEXT_MAX);
    }
    txt_write($TEXT_FILE_2, $txt2);
  } else {
    $txt2 = txt_read($TEXT_FILE_2);
  }

  print $CGI->header(-type => 'text/html',
		     -charset => 'utf-8');
  $txt1 = escape_html($txt1);
  $txt2 = escape_html($txt2);
  print <<"EOT";
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta name="robots" content="noindex,nofollow" />
<meta name="viewport" content="width=device-width,initial-scale=1" />

<title>Dual Memo</title>
<!-- dual_memo.cgi version $VERSION .
     You can get it from https://github.com/JRF-2018/memo_cgi . -->
<style type="text/css">
</style>
<script type="text/javascript">
<!--
function resizeTextareaIfSmartphone() {
  if (window.matchMedia
      && window.matchMedia('(max-device-width: 640px)').matches) {
    var txt1 = document.getElementById("txt1");
    var txt2 = document.getElementById("txt2");
    txt1.style.width = "90%";
    txt2.style.width = "90%";
    txt1.style.height = Math.floor(window.innerHeight *  0.4) + "px";
    txt2.style.height = Math.floor(window.innerHeight *  0.4) + "px";
  }
}

function init() {
  document.getElementById('flag1').value = 0;
  document.getElementById('flag2').value = 0;
  resizeTextareaIfSmartphone();
}

function changeText(id) {
  document.getElementById(id).value = 1;
}

-->
</script>
</head>
<body onLoad="init()">
<form action="dual_memo.cgi" method="post">
<textarea id="txt1" name="txt1" rows="15" cols="80"
onChange="changeText('flag1')">$txt1</textarea>
<br />
<textarea id="txt2" name="txt2" rows="15" cols="80"
onChange="changeText('flag2')">$txt2</textarea>
<br/>
<!--
Pass: <input type="password" name="pass" />
-->
<button type="submit" name="cmd" value="submit">Submit</button>
<button type="submit" name="cmd" value="reload">Reload</button>
<input type="hidden" id="flag1" name="flag1" value="1" />
<input type="hidden" id="flag2" name="flag2" value="1" />
</form>
</body>
</html>
EOT
}

main();
exit(0);
