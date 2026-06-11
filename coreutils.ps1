#Set-Alias cat C:\"Program Files"\coreutils\bin\cat.exe
#if (Test-Path 'C:\Program Files\coreutils\bin\cp.exe') {
#       Remove-Item Alias:cp -Force -ErrorAction SilentlyContinue
#       Set-Alias -Name cp -Value C:\"Program Files"\coreutils\bin\cp.exe -Option AllScope
#}
#Set-Alias ls C:\"Program Files"\coreutils\bin\ls.exe

Remove-Item Alias:cp -Force -ErrorAction SilentlyContinue
Remove-Item Alias:echo -Force -ErrorAction SilentlyContinue
Remove-Item Alias:sort -Force -ErrorAction SilentlyContinue
Remove-Item Alias:sleep -Force -ErrorAction SilentlyContinue
Remove-Item Alias:tee -Force -ErrorAction SilentlyContinue

Set-Alias arch 'C:\Program Files\coreutils\bin\arch.exe'
Set-Alias b2sum 'C:\Program Files\coreutils\bin\b2sum.exe'
Set-Alias base32 'C:\Program Files\coreutils\bin\base32.exe'
Set-Alias base64 'C:\Program Files\coreutils\bin\base64.exe'
Set-Alias basename 'C:\Program Files\coreutils\bin\basename.exe'
Set-Alias basenc 'C:\Program Files\coreutils\bin\basenc.exe'
Set-Alias cat 'C:\Program Files\coreutils\bin\cat.exe'
Set-Alias cksum 'C:\Program Files\coreutils\bin\cksum.exe'
Set-Alias comm 'C:\Program Files\coreutils\bin\comm.exe'
Set-Alias cp 'C:\Program Files\coreutils\bin\cp.exe' -Option AllScope
Set-Alias csplit 'C:\Program Files\coreutils\bin\csplit.exe'
Set-Alias cut 'C:\Program Files\coreutils\bin\cut.exe'
Set-Alias date 'C:\Program Files\coreutils\bin\date.exe'
Set-Alias df 'C:\Program Files\coreutils\bin\df.exe'
Set-Alias dirname 'C:\Program Files\coreutils\bin\dirname.exe'
Set-Alias du 'C:\Program Files\coreutils\bin\du.exe'
Set-Alias echo 'C:\Program Files\coreutils\bin\echo.exe' -Option AllScope
Set-Alias env 'C:\Program Files\coreutils\bin\env.exe'
Set-Alias expr 'C:\Program Files\coreutils\bin\expr.exe'
Set-Alias factor 'C:\Program Files\coreutils\bin\factor.exe'
Set-Alias false 'C:\Program Files\coreutils\bin\false.exe'
Set-Alias find 'C:\Program Files\coreutils\bin\find.exe'
Set-Alias fmt 'C:\Program Files\coreutils\bin\fmt.exe'
Set-Alias fold 'C:\Program Files\coreutils\bin\fold.exe'
Set-Alias grep 'C:\Program Files\coreutils\bin\grep.exe'
Set-Alias head 'C:\Program Files\coreutils\bin\head.exe'
Set-Alias hostname 'C:\Program Files\coreutils\bin\hostname.exe'
Set-Alias join 'C:\Program Files\coreutils\bin\join.exe'
Set-Alias link 'C:\Program Files\coreutils\bin\link.exe'
Set-Alias ln 'C:\Program Files\coreutils\bin\ln.exe'
Set-Alias ls 'C:\Program Files\coreutils\bin\ls.exe'
Set-Alias md5sum 'C:\Program Files\coreutils\bin\md5sum.exe'
Set-Alias mkdir 'C:\Program Files\coreutils\bin\mkdir.exe'
Set-Alias mktemp 'C:\Program Files\coreutils\bin\mktemp.exe'
Set-Alias mv 'C:\Program Files\coreutils\bin\mv.exe'
Set-Alias nl 'C:\Program Files\coreutils\bin\nl.exe'
Set-Alias nproc 'C:\Program Files\coreutils\bin\nproc.exe'
Set-Alias numfmt 'C:\Program Files\coreutils\bin\numfmt.exe'
Set-Alias od 'C:\Program Files\coreutils\bin\od.exe'
Set-Alias pathchk 'C:\Program Files\coreutils\bin\pathchk.exe'
Set-Alias pr 'C:\Program Files\coreutils\bin\pr.exe'
Set-Alias printenv 'C:\Program Files\coreutils\bin\printenv.exe'
Set-Alias printf 'C:\Program Files\coreutils\bin\printf.exe'
Set-Alias ptx 'C:\Program Files\coreutils\bin\ptx.exe'
Set-Alias pwd 'C:\Program Files\coreutils\bin\pwd.exe'
Set-Alias readlink 'C:\Program Files\coreutils\bin\readlink.exe'
Set-Alias realpath 'C:\Program Files\coreutils\bin\realpath.exe'
Set-Alias rm 'C:\Program Files\coreutils\bin\rm.exe'
Set-Alias rmdir 'C:\Program Files\coreutils\bin\rmdir.exe'
Set-Alias seq 'C:\Program Files\coreutils\bin\seq.exe'
Set-Alias sha1sum 'C:\Program Files\coreutils\bin\sha1sum.exe'
Set-Alias sha224sum 'C:\Program Files\coreutils\bin\sha224sum.exe'
Set-Alias sha256sum 'C:\Program Files\coreutils\bin\sha256sum.exe'
Set-Alias sha384sum 'C:\Program Files\coreutils\bin\sha384sum.exe'
Set-Alias sha512sum 'C:\Program Files\coreutils\bin\sha512sum.exe'
Set-Alias shuf 'C:\Program Files\coreutils\bin\shuf.exe'
Set-Alias sleep 'C:\Program Files\coreutils\bin\sleep.exe' -Option AllScope
Set-Alias sort 'C:\Program Files\coreutils\bin\sort.exe' -Option AllScope
Set-Alias split 'C:\Program Files\coreutils\bin\split.exe'
Set-Alias stat 'C:\Program Files\coreutils\bin\stat.exe'
Set-Alias sum 'C:\Program Files\coreutils\bin\sum.exe'
Set-Alias tac 'C:\Program Files\coreutils\bin\tac.exe'
Set-Alias tail 'C:\Program Files\coreutils\bin\tail.exe'
Set-Alias tee 'C:\Program Files\coreutils\bin\tee.exe' -Option AllScope
Set-Alias test 'C:\Program Files\coreutils\bin\test.exe'
Set-Alias touch 'C:\Program Files\coreutils\bin\touch.exe'
Set-Alias tr 'C:\Program Files\coreutils\bin\tr.exe'
Set-Alias true 'C:\Program Files\coreutils\bin\true.exe'
Set-Alias truncate 'C:\Program Files\coreutils\bin\truncate.exe'
Set-Alias tsort 'C:\Program Files\coreutils\bin\tsort.exe'
Set-Alias unexpand 'C:\Program Files\coreutils\bin\unexpand.exe'
Set-Alias uniq 'C:\Program Files\coreutils\bin\uniq.exe'
Set-Alias unlink 'C:\Program Files\coreutils\bin\unlink.exe'
Set-Alias uptime 'C:\Program Files\coreutils\bin\uptime.exe'
Set-Alias wc 'C:\Program Files\coreutils\bin\wc.exe'
Set-Alias xargs 'C:\Program Files\coreutils\bin\xargs.exe'
Set-Alias yes 'C:\Program Files\coreutils\bin\yes.exe'
