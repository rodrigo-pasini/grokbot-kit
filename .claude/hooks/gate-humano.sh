#!/usr/bin/env bash
# Gates humanos: o agente faz push de branch e abre PR sozinho, e para no que é do Rodrigo (AD-050, door 6).
#
# PreToolUse em Bash. Para cada pedaço do comando (separado por &&, ||, ;, | ou quebra de linha):
#   deny  git push que alcança main (refspec main, HEAD:main, ou sem refspec com a branch atual main), --all, --mirror
#   ask   gh pr merge, git tag, git push de tag (v*, refs/tags/, --tags), gh release, gh api com protection/environments
#   allow git push de branch <tipo>/<issue>/<slug> (sem --delete nem --force) e gh pr create, só num comando simples
#         (allow vale para o comando todo)
# deny vence ask, que vence allow. Nenhum dos casos: sai sem saída e vale a permissão normal.
set -uo pipefail

input="$(cat)"
cmd="$(jq -r '.tool_input.command // empty' <<<"$input")"
[ -z "$cmd" ] && exit 0
cwd="$(jq -r '.cwd // empty' <<<"$input")"
cwd="${cwd:-$PWD}"

branch_ok() {
  [[ $1 =~ ^(feat|fix|refactor|perf|test|docs|chore|build|ci)/[0-9]+/[a-z0-9][a-z0-9-]*$ ]] ||
    [[ $1 =~ ^chore/release/[0-9]+\.[0-9]+\.[0-9]+$ ]] || [[ $1 =~ ^dependabot/ ]]
}

current_branch() { git -C "$cwd" branch --show-current 2>/dev/null; }

# Decide um git push; args sem o "git push". Imprime deny, ask, allow ou nada.
push_decision() {
  local pos=() skip=0 risky=0 a
  for a in "$@"; do
    if [ "$skip" = 1 ]; then skip=0; continue; fi
    case "$a" in
      --tags) echo ask; return ;;
      --all | --mirror) echo deny; return ;;
      -d | --delete | -f | --force | --force-with-lease*) risky=1 ;;
      -o | --push-option | --repo | --receive-pack | --exec) skip=1 ;;
      -*) ;;
      *) pos+=("$a") ;;
    esac
  done
  local refs=("${pos[@]:1}") cur
  cur="$(current_branch)"
  [ "${#refs[@]}" = 0 ] && refs=("$cur")
  local result=allow ref src dst
  for ref in "${refs[@]}"; do
    ref="${ref#+}"
    src="${ref%%:*}"
    if [[ $ref == *:* ]]; then dst="${ref#*:}"; else dst="$src"; fi
    [ "$dst" = HEAD ] && dst="$cur"
    dst="${dst#refs/heads/}"
    if [ "$dst" = main ]; then echo deny; return; fi
    if [[ $dst == v* || $dst == refs/tags/* || $src == refs/tags/* ]]; then result=ask; continue; fi
    if [ "$result" = allow ] && ! branch_ok "$dst"; then result=none; fi
  done
  [ "$result" = allow ] && [ "$risky" = 1 ] && result=none
  [ "$result" != none ] && echo "$result"
}

# Decide um pedaço do comando.
segment_decision() {
  local w=("$@") i=1 sub=""
  case "${w[0]:-}" in
    git)
      while [ "$i" -lt "${#w[@]}" ]; do
        case "${w[$i]}" in
          -C | -c) i=$((i + 2)) ;;
          -*) i=$((i + 1)) ;;
          *) sub="${w[$i]}"; break ;;
        esac
      done
      case "$sub" in
        tag) echo ask ;;
        push) push_decision "${w[@]:$((i + 1))}" ;;
      esac
      ;;
    gh)
      case "${w[1]:-} ${w[2]:-}" in
        "pr merge") echo ask ;;
        "pr create") echo allow ;;
        release\ *) echo ask ;;
        api\ *) [[ " ${w[*]} " == *protection* || " ${w[*]} " == *environments* ]] && echo ask ;;
      esac
      ;;
  esac
}

simple=1
case "$cmd" in *[\;\&\|\<\>\$\`]* | *$'\n'*) simple=0 ;; esac

decisions=""
while IFS= read -r segment; do
  read -ra words <<<"$segment"
  [ "${#words[@]}" = 0 ] && continue
  decisions+="$(segment_decision "${words[@]}") "
done < <(sed -E 's/(&&|\|\||;|\|)/\n/g' <<<"$cmd")

reply() {
  jq -n --arg d "$1" --arg r "$2" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:$d,permissionDecisionReason:$r}}'
}

case "$decisions" in
  *deny*) reply deny "Push para main é negado: main só recebe merge de PR, feito pelo Rodrigo (AD-050). Faça push da branch <tipo>/<issue>/<slug> e abra o PR." ;;
  *ask*) reply ask "Merge, tag, release e mudança de proteção ou environment são passos do Rodrigo (AD-050): confirme antes de seguir." ;;
  *allow*) [ "$simple" = 1 ] && reply allow "Push de branch de feature e abertura de PR o agente faz sozinho (AD-050)." ;;
esac
exit 0
