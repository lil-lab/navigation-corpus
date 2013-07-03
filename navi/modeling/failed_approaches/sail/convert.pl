#!/opt/local/bin/perl

open(IN,"../navigation-sail/data/semantic/SingleSentences-sail.xml");

$id_num=0;

while ($line = <IN>){
    if ($line =~ /id\="(\d+)\-/){
	if ($1>$id_num){
	    $id_num = $1;
	    print "// $id_num\n";
	}
    }

    if ($line =~ /\<nl lang=\"en\"\> (.*) <\/nl>/){
	print "$1\n"
    }

    if ($line =~ /\<mrl lang=\"sail\"\>/){	
	$mr = "";
	while (($line = <IN>) && ($line !~ /mrl/)){
	    chomp($line);
	    $line=~s/^\s+//;
	    $mr .= $line." ";
	}

	$mr=~s/NULL/NULL:t/;

	$mr=~s/Travel \(([^\)]+)\) , Verify \(([^\)]+)\)/Travel \($1 , $2\)/g;
	$mr=~s/Turn \(([^\)]+)\) , Verify \(([^\)]+)\)/Turn \($1 , $2\)/g;
	$mr=~s/\(  , /(/g;

	while ($mr =~ /((\w+) \(([^\)]+)\))/){
	    $match=$1;
	    $pred = $2;
	    $pred.=":a";
	    $args = $3;
	    $end="";
	    if ($args =~ /,/){
		$pred.=" [and:t ";
		$end=")";
	    }
	    $mr=~s/\Q$match\E/\($pred $args\)$end/;
	}
	$mr=~s/\[/\(/g;

	
	$mr =~ s/(\w+)\: (\w) ,?/\(=:t $1\:e $2\:e)/g;
	$mr =~ s/(\w+)\: ([\w\-]+ ?[\w\-]+) ?,?/\(=:t $1\:e $2\:e)/g;
	$mr =~ s/ (\w+) (\w+)\:e/ $1_$2\:e/g;

	$mr =~ s/RIGHT /\(=:t heading:e right:e\)/;
	$mr =~ s/LEFT /\(=:t heading:e left:e\)/;

	if ($mr=~/,/){
	    $mr =~ s/,//g;
	    $mr = "(do-seq:a $mr)";
	}

	do {} while($mr =~ s/  / /g);
	$mr =~ s/ \)/\)/g;
	$mr =~ s/ \)/\)/g;

	$mr =~ s/(\w+):a\)/$1:a true:t\)/g;

	$mr = lc $mr;



	print "$mr\n\n";
    }

}


