#!/usr/bin/bash
function main(){
    if curl --version >/dev/null 2>/dev/null
    then
        function http_get(){ curl -s "$1"; }
        function http_post(){ curl -s "$1" -d "$2"; }
    else
        function http_get(){ wget -qO- "$1"; }
        function http_post(){ wget -qO- "$1" --post-data="$2"; }
    fi
    tmppipe1="$(mktemp -u)"
    # tmppipe2="$(mktemp -u)"
    mkfifo -m 600 "$tmppipe1"
    # mkfifo -m 600 "$tmppipe2"
    function send1(){
        IFS=''
        while :
        do
            read -rn 1024 -t 0.1 text
            read_exit_code="$?"
            if [ "$read_exit_code" -ne 0 -a "$read_exit_code" -le 128 ]
            then
                break
            fi
            if [ "$read_exit_code" -eq 0 ]
            then
                text="$text"$'\n'
            fi
            if ! [ -z "$text" ]
            then
                if ! http_post "$REMOTE_URL"_client "$(printf '%s' "$text" | base64)"
                then
                    break
                fi
            fi
        done
        http_post "$REMOTE_URL"_client "^^^^"
    }
    function recv(){
        while http_get "$REMOTE_URL"_server
        do
            :
        done
    }
    echo "This terminal is now controlled by your friend."
    send1 < "$tmppipe1" &
    if script --version >/dev/null 2>/dev/null
    then
        recv | script -q -f "$tmppipe1"
    else
        recv | script -q -F "$tmppipe1"
    fi
    echo "Your friend left the terminal."
}
main

