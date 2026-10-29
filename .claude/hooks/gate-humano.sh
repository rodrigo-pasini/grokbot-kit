#!/usr/bin/env bash
# Gates humanos: o agente faz push de branch e abre PR sozinho, e para no que é do Rodrigo (AD-050, door 6).
#
# PreToolUse em Bash. Para cada pedaço do comando (separado por &&, ||, ;, | ou quebra de linha):
#   deny  git push que alcança main (refspec main, HEAD:main, ou sem refspec com a branch atual main), --all, --mirror
#   ask   gh pr merge, git tag, git push de tag (v*, refs/tags/, --tags), gh release, gh api com protection/environments
#   allow git push de branch <tipo>/<issue>/<slug> (sem --delete nem --force) e gh pr create, só num comando simples
#         (allow vale para o comando todo)
# O comando é cortado fora das aspas, também em ( ) de subshell e em & de segundo plano; um $( ) fica inteiro na palavra
# do comando de fora, e o conteúdo de cada $( ) e crase, entre aspas ou não, é decidido também como um comando à parte.
# Antes de decidir, tira aspas e barras invertidas das palavras e os prefixos VAR=valor, env e command, e lê
# /usr/bin/git como git. Push para outro repositório (GIT_DIR=, GIT_WORK_TREE=, -C, --git-dir, --work-tree) não ganha
# allow: o HEAD e a branch atual são lidos do cwd.
# Falha fechado com ask quando não lê o comando: refspec de push com substituição ($ ou crase), ou git/gh fora da
# primeira palavra (bash -c, sudo, xargs, echo ... | sh) junto de push, tag, merge, release ou api.
# deny vence ask, que vence o ask de falha fechada, que vence allow. Nenhum dos casos: sai sem saída e vale a permissão normal.
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

# 1 quando o pedaço em análise aponta o git para outro repositório.
redirect=0

# Decide um git push; args sem o "git push". Imprime deny, ask, allow ou nada.
push_decision() {
  local pos=() skip=0 risky=0 tags=0 a
  for a in "$@"; do
    if [ "$skip" = 1 ]; then skip=0; continue; fi
    case "$a" in
      --tags | --follow-tags) tags=1 ;;
      --all | --mirror) echo deny; return ;;
      -d | --delete | -f | --force | --force-with-lease*) risky=1 ;;
      -o | --push-option | --repo | --receive-pack | --exec) skip=1 ;;
      -[!-]*) [[ $a == *[fd]* ]] && risky=1 ;;
      -*) ;;
      *) pos+=("$a") ;;
    esac
  done
  local refs=("${pos[@]:1}") cur
  cur="$(current_branch)"
  [ "${#refs[@]}" = 0 ] && refs=("$cur")
  local result=allow ref src dst
  for ref in "${refs[@]}"; do
    if [[ $ref == *[\$\`]* ]]; then [ "$result" = ask ] || result=unread; continue; fi
    ref="${ref#+}"
    src="${ref%%:*}"
    if [[ $ref == *:* ]]; then dst="${ref#*:}"; else dst="$src"; fi
    [ "$dst" = HEAD ] && dst="$cur"
    dst="${dst#refs/heads/}"
    if [ "$dst" = main ]; then echo deny; return; fi
    if [[ $dst == v* || $dst == refs/tags/* || $src == refs/tags/* ]]; then result=ask; continue; fi
    if [ "$result" = allow ] && ! branch_ok "$dst"; then result=none; fi
  done
  [ "$tags" = 1 ] && result=ask
  [ "$result" = allow ] && [ "$risky$redirect" != 00 ] && result=none
  [ "$result" != none ] && echo "$result"
}

# Decide um pedaço do comando.
segment_decision() {
  local w=("$@") i=1 sub="" x tool=0 verb=0
  redirect=0
  while [ "${#w[@]}" -gt 1 ]; do
    case "${w[0]}" in
      GIT_DIR=* | GIT_WORK_TREE=*) redirect=1; w=("${w[@]:1}") ;;
      env | command | [A-Za-z_]*=*) w=("${w[@]:1}") ;;
      *) break ;;
    esac
  done
  w[0]="${w[0]##*/}"
  case "${w[0]}" in
    git)
      while [ "$i" -lt "${#w[@]}" ]; do
        case "${w[$i]}" in
          -C) redirect=1; i=$((i + 2)) ;;
          -c | --config-env)
            x="${w[$((i + 1))]:-}"
            [[ ${x,,} == alias.* ]] && { echo unread; return; }
            i=$((i + 2))
            ;;
          --git-dir | --work-tree | --namespace) redirect=1; i=$((i + 2)) ;;
          --git-dir=* | --work-tree=* | --namespace=*) redirect=1; i=$((i + 1)) ;;
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
      # As duas primeiras palavras que não são flag (gh pr -R o/r merge -> pr merge).
      local g=() j=1
      while [ "$j" -lt "${#w[@]}" ] && [ "${#g[@]}" -lt 2 ]; do
        case "${w[$j]}" in
          -R | --repo) j=$((j + 2)) ;;
          -*) j=$((j + 1)) ;;
          *) g+=("${w[$j]}"); j=$((j + 1)) ;;
        esac
      done
      case "${g[0]:-} ${g[1]:-}" in
        "pr merge") echo ask ;;
        "pr create") echo allow ;;
        release\ *) echo ask ;;
        api\ *) [[ " ${w[*]} " =~ protection|environments|/merge|mergePullRequest|releases|git/refs ]] && echo ask ;;
      esac
      ;;
    *)
      for x in "${w[@]}"; do
        x="${x//\`/}"
        case "${x##*/}" in
          git | gh) tool=1 ;;
          push | tag | merge | release | api) verb=1 ;;
        esac
      done
      [ "$tool$verb" = 11 ] && echo unread
      ;;
  esac
}

simple=1
case "$cmd" in *[\;\&\|\<\>\$\`]* | *$'\n'*) simple=0 ;; esac

# Um pedaço por linha: corta em &&, ||, ;, |, &, ( e ) fora de aspas; $( ) fica inteiro; \ escapa o próximo caractere.
split_segments() {
  awk '{
    q = ""; out = ""; depth = 0; n = length($0)
    for (i = 1; i <= n; i++) {
      c = substr($0, i, 1)
      if (q == "\047") { out = out c; if (c == q) q = ""; continue }
      if (c == "\\") { out = out c substr($0, i + 1, 1); i++; continue }
      if (q == "\"") { out = out c; if (c == q) q = ""; continue }
      if (c == "\047" || c == "\"") { q = c; out = out c; continue }
      if (c == "$" && substr($0, i + 1, 1) == "(") { depth++; out = out "$("; i++; continue }
      if (c == ")" && depth > 0) { depth--; out = out c; continue }
      if (c == ";" || c == "|" || c == "&" || c == "(" || c == ")") {
        print out; out = ""
        nx = substr($0, i + 1, 1)
        if ((c == "|" || c == "&") && nx == c) i++
        continue
      }
      out = out c
    }
    print out
  }'
}

# O conteúdo de cada $( ) sem $( ) dentro e de cada crase, um por linha, onde quer que estejam (aspas duplas não impedem
# a substituição). Um $( ) aninhado é alcançado pelo de dentro.
substitutions() {
  grep -oE '\$\([^()]*\)|`[^`]*`' <<<"$cmd" | sed -E 's/^\$\(//; s/\)$//; s/^`//; s/`$//'
}

decisions=""
while IFS= read -r segment; do
  read -ra words <<<"$segment"
  [ "${#words[@]}" = 0 ] && continue
  words=("${words[@]//[\"\'\\]/}")
  decisions+="$(segment_decision "${words[@]}") "
done < <(
  split_segments <<<"$cmd"
  substitutions | split_segments
)

reply() {
  jq -n --arg d "$1" --arg r "$2" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:$d,permissionDecisionReason:$r}}'
}

case "$decisions" in
  *deny*) reply deny "Push para main é negado: main só recebe merge de PR, feito pelo Rodrigo (AD-050). Faça push da branch <tipo>/<issue>/<slug> e abra o PR." ;;
  *ask*) reply ask "Merge, tag, release e mudança de proteção ou environment são passos do Rodrigo (AD-050): confirme antes de seguir." ;;
  *unread*) reply ask "O gate não lê este comando (substituição no refspec, ou git/gh dentro de outro comando): confirme que ele não faz push para main, merge, tag nem release (AD-050)." ;;
  *allow*) [ "$simple" = 1 ] && reply allow "Push de branch de feature e abertura de PR o agente faz sozinho (AD-050)." ;;
esac
exit 0
