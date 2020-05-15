#!/usr/bin/perl
our $VERSION = "0.0.7"; # Time-stamp: <2020-05-15T17:41:23Z>";

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

our $TEXT_FILE_1 = "bbs_notice.txt";
our $TEXT_FILE_2 = "bbs.txt";
#our $PASSWORD = "test";
our $TEXT_MAX = 1024 * 1024;
our $NAME_MAX = 64;
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

sub txt_prepend {
  my ($file, $txt) = @_;
  sysopen(my $fh, $file, O_RDWR | O_CREAT)
    or die "Cannot open $file: $!";
  flock($fh, LOCK_EX)
    or die "Cannot lock $file: $!";
  binmode($fh);
  $txt = $txt . decode('UTF-8', join("", <$fh>));
  while (length($txt) > $TEXT_MAX) {
    $txt = substr($txt, 0, -1);
    $txt =~ s/[^\n]+$//s;
  }
  seek($fh, 0, SEEK_SET)
    or die "Cannot seek $file: $!";
  my $btxt = encode('UTF-8', $txt);
  print $fh $btxt
    or die "Cannot Write $file: $!";
  truncate($fh, length($btxt));
  flock($fh, LOCK_UN);
  close($fh);
  return $txt;
}

sub main {
  my $cmd = $CGI->param('cmd') || 'read';
  my $txt1;
  my $txt2;

  my $name = decode('UTF-8', $CGI->cookie('name') || '');
  if (length($name) > $NAME_MAX) {
    $name = substr($name, 0, $NAME_MAX);
  }

  if ($cmd eq 'write_notice') {
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

  if ($cmd eq 'add') {
    # my $pass = $CGI->param('pass');
    # die "Wrong password." if ! defined $pass || $pass ne $PASSWORD;
    $name = $CGI->param('name') || "";
    $name = decode('UTF-8', $name);
    if (length($name) > $NAME_MAX) {
      $name = substr($name, 0, $NAME_MAX);
    }
    $txt2 = $CGI->param('txt2') || "";
    $txt2 = decode('UTF-8', $txt2);
    $txt2 = "(" . (($name ne "")? $name : '?') . ") " . $txt2;
    if (length($txt2) > $TEXT_MAX - 1) {
      $txt2 = substr($txt2, 0, $TEXT_MAX - 1);
    }
    $txt2 .= "\n" if $txt2 !~ /\n$/s;
    $txt2 = txt_prepend($TEXT_FILE_2, $txt2);
  } elsif ($cmd eq 'clear') {
    # my $pass = $CGI->param('pass');
    # die "Wrong password." if ! defined $pass || $pass ne $PASSWORD;
    txt_write($TEXT_FILE_2, "");
    $txt2 = "";
  } else {
    $txt2 = txt_read($TEXT_FILE_2);
  }

  my $ncookie = $CGI->cookie(-name => 'name',
			     -value => encode('UTF-8', $name),
			     -expires => '+1y');
  print $CGI->header(-type => 'text/html',
		     -charset => 'utf-8',
		     -cookie => [$ncookie]);
  $name = escape_html($name);
  $txt1 = escape_html($txt1);
  $txt2 = escape_html($txt2);
  print <<"EOT";
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta name="robots" content="noindex,nofollow" />
<meta name="viewport" content="width=device-width,initial-scale=1" />

<title>Simple BBS</title>
<!-- simple_bbs.cgi version $VERSION -->
<style type="text/css">
</style>
<script type="text/javascript">
<!--
function resizeTextareaIfSmartphone() {
  if (window.matchMedia
      && window.matchMedia('(max-device-width: 640px)').matches) {
    var txt1 = document.getElementById("txt1");
    var txt2 = document.getElementById("txt2");
    var txt3 = document.getElementById("txt3");
    txt1.style.width = "90%";
    txt2.style.width = "90%";
    txt3.style.width = "90%";
    txt1.style.height = Math.floor(window.innerHeight *  0.3) + "px";
    txt3.style.height = Math.floor(window.innerHeight *  0.4) + "px";
  }
}

function init() {
  resizeTextareaIfSmartphone();
}

-->
</script>
</head>
<body onLoad="init()">
<form action="simple_bbs.cgi" method="post">
<textarea id="txt1" name="txt1" rows="10" cols="80">$txt1</textarea>
<br />
<!--
Pass: <input type="password" size="8" name="pass" />
-->
<button type="submit" name="cmd" value="write_notice">Change above</button>
<button type="submit" name="cmd" value="read">Reload</button>
<br />
<textarea id="txt2" name="txt2" rows="2" cols="80"></textarea>
<br />
by <input type="text" size="8" name="name" id="name" value="$name" />
<button type="submit" name="cmd" value="add">Add</button>
<button type="submit" name="cmd" value="clear">Clear below</button>
<br />
<textarea id="txt3" rows="25" cols="80" readonly>$txt2</textarea>
</form>
</body>
</html>
EOT
}

main();
exit(0);
