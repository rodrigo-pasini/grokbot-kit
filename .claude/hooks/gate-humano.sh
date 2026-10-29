#!/usr/bin/env bash
# Gates humanos: o agente faz push de branch e abre PR sozinho, e para no que é do Rodrigo (AD-050, door 6).
#
# PreToolUse em Bash. Para cada pedaço do comando (separado por &&, ||, ;, |, &, ( ), ou quebra de linha, fora de aspas):
#   deny  git push que alcança main (refspec main, HEAD:main, ou sem refspec com a branch atual main), --all, --mirror
#   ask   gh pr merge, git tag, git push de tag (v*, refs/tags/, --tags), gh release, gh api com protection/environments
#   allow git push de branch <tipo>/<issue>/<slug> (sem --delete nem --force) e gh pr create, só num comando simples
#         (allow vale para o comando todo)
# Antes de decidir, tira aspas e barras invertidas das palavras e os prefixos VAR=valor, env e command, e lê
# /usr/bin/git como git. Push para outro repositório (GIT_DIR=, GIT_WORK_TREE=, -C, --git-dir, --work-tree) não ganha
# allow: o HEAD e a branch atual são lidos do cwd.
# O gate não interpreta o shell, e falha fechado com ask: num segundo passe, cada trecho que o bash executa (fora de
# aspas, e o que está dentro de $( ) ou crase, também entre aspas duplas) e que cita git ou gh junto de push, tag, merge,
# release ou api sem decisão limpa pede confirmação. Texto que o bash não executa (aspas simples, aspas duplas sem
# substituição, corpo de heredoc) não conta, a menos que o comando passe texto a um shell (bash, sh, eval, sudo, xargs).
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

# Decide um git push; args sem o "git push". Imprime deny, ask, allow ou clean (lido, sem decisão).
push_decision() {
  local pos=() skip=0 risky=0 tags=0 a
  for a in "$@"; do
    if [ "$skip" = 1 ]; then skip=0; continue; fi
    [[ $a =~ ^[0-9]*[\<\>] ]] && continue
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
    # Q: texto entre aspas com substituição, no segundo passe.
    if [[ $ref == *[\$\`]* || $ref == Q ]]; then [ "$result" = ask ] || result=unread; continue; fi
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
  if [ "$result" = none ]; then echo clean; else echo "$result"; fi
}

# Decide um pedaço do comando. clean: um comando git ou gh lido por inteiro, sem decisão.
segment_decision() {
  local w=("$@") i=1 sub="" x
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
          --config-env=*)
            x="${w[$i]#--config-env=}"
            [[ ${x,,} == alias.* ]] && { echo unread; return; }
            i=$((i + 1))
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
        *) echo clean ;;
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
        api\ *)
          if [[ " ${w[*]} " =~ protection|environments|/merge|mergePullRequest|enablePullRequestAutoMerge|releases|git/refs ]]; then
            echo ask
          else
            echo clean
          fi
          ;;
        *) echo clean ;;
      esac
      ;;
  esac
}

simple=1
case "$cmd" in *[\;\&\|\<\>\$\`]* | *$'\n'*) simple=0 ;; esac

# Corta o comando em pedaços, um por linha, conforme o modo:
#   A  pedaços para decidir: corta em &&, ||, ;, |, &, ( ), quebra de linha, fora de aspas; $( ) fica inteiro; corpos
#      de heredoc saem (são dados)
#   B  o que o bash executa: aspas simples e aspas duplas sem substituição viram Q (uma palavra sem espaço fica); o
#      conteúdo de $( ) e crase, também entre aspas duplas e em heredoc sem aspas no delimitador, vira pedaço próprio
#   R  como B, mas o texto entre aspas e de heredoc fica inteiro: o comando passa texto a um shell
VIEW_AWK='
function regions(t,   out, k, n, ch, d, r) {
  out = ""; n = length(t)
  for (k = 1; k <= n; k++) {
    ch = substr(t, k, 1)
    if (ch == "\\") { k++; continue }
    if (ch == "$" && substr(t, k + 1, 1) == "(") {
      d = 1; k += 2; r = ""
      while (k <= n) {
        ch = substr(t, k, 1)
        if (ch == "(") d++
        else if (ch == ")") { d--; if (d == 0) break }
        r = r ch; k++
      }
      out = out "\n" r "\n"; continue
    }
    if (ch == "`") {
      k++; r = ""
      while (k <= n && substr(t, k, 1) != "`") { r = r substr(t, k, 1); k++ }
      out = out "\n" r "\n"
    }
  }
  return out
}
function quoted(t, single) {
  if (mode == "R") return " " t " "
  if (t !~ /[ \t\n$`]/) return t
  if (single) return " Q "
  return " Q \n" scan(regions(t)) "\n"
}
function scan(s,   out, n, i, j, c, ch, t, d, q, dash, np, pd, pq, pdash, h, e, line, cmp, body, depth) {
  out = ""; n = length(s); i = 1; np = 0; depth = 0
  while (i <= n) {
    c = substr(s, i, 1)
    if (c == "\\") { out = out (mode == "A" ? c : "") substr(s, i + 1, 1); i += 2; continue }
    if (c == "\047" || c == "\"") {
      j = i + 1; t = ""
      while (j <= n) {
        ch = substr(s, j, 1)
        if (c == "\"" && ch == "\\") { t = t ch substr(s, j + 1, 1); j += 2; continue }
        if (ch == c) break
        t = t ch; j++
      }
      out = out (mode == "A" ? c t c : quoted(t, c == "\047"))
      i = j + 1; continue
    }
    if (c == "<" && substr(s, i + 1, 1) == "<" && substr(s, i + 2, 1) != "<" && substr(s, i - 1, 1) != "<") {
      j = i + 2; dash = 0; q = 0; d = ""
      if (substr(s, j, 1) == "-") { dash = 1; j++ }
      while (substr(s, j, 1) == " " || substr(s, j, 1) == "\t") j++
      ch = substr(s, j, 1)
      if (ch == "\047" || ch == "\"") {
        q = 1; j++
        while (j <= n && substr(s, j, 1) != ch) { d = d substr(s, j, 1); j++ }
        j++
      } else {
        if (ch == "\\") { q = 1; j++ }
        while (j <= n && substr(s, j, 1) ~ /[A-Za-z0-9_]/) { d = d substr(s, j, 1); j++ }
      }
      if (d != "") { np++; pd[np] = d; pq[np] = q; pdash[np] = dash }
      out = out " "; i = j; continue
    }
    if (c == "\n" && np > 0) {
      out = out "\n"; i++
      for (h = 1; h <= np; h++) {
        body = ""
        while (i <= n) {
          e = index(substr(s, i), "\n")
          line = e ? substr(s, i, e - 1) : substr(s, i)
          i += e ? e : length(line) + 1
          cmp = line
          if (pdash[h]) sub(/^\t+/, "", cmp)
          if (cmp == pd[h]) break
          body = body line "\n"
        }
        if (mode == "R") out = out body "\n"
        else if (mode == "B" && !pq[h]) out = out " Q \n" scan(regions(body)) "\n"
      }
      np = 0; continue
    }
    if (mode == "A" && c == "$" && substr(s, i + 1, 1) == "(") { depth++; out = out "$("; i += 2; continue }
    if (mode == "A" && c == ")" && depth > 0) { depth--; out = out c; i++; continue }
    if (mode != "A" && c == "$" && substr(s, i + 1, 1) == "(") { out = out "\n"; i += 2; continue }
    if (c == ";" || c == "|" || c == "&" || c == "(" || c == ")" || c == "\n" || (mode != "A" && c == "`")) {
      out = out "\n"; i++; continue
    }
    out = out c; i++
  }
  return out
}
{ s = s $0 "\n" }
END { printf "%s\n", scan(s) }
'
view() { awk -v mode="$1" "$VIEW_AWK" <<<"$cmd"; }

# 0 quando o texto cita git ou gh junto de um verbo que o gate decide.
mentions() {
  local x tool=0 verb=0
  for x in $(tr -c 'A-Za-z0-9_./-' ' ' <<<"$1"); do
    case "${x##*/}" in
      git | gh) tool=1 ;;
      push | tag | merge | release | api) verb=1 ;;
    esac
  done
  [ "$tool$verb" = 11 ]
}

decisions=""
while IFS= read -r segment; do
  read -ra words <<<"$segment"
  [ "${#words[@]}" = 0 ] && continue
  words=("${words[@]//[\"\'\\]/}")
  decisions+="$(segment_decision "${words[@]}") "
done < <(view A)

# Segundo passe (falha fechado). Um comando que passa texto a um shell lê o texto todo.
executed="$(view B)"
for x in $(tr -c 'A-Za-z0-9_./-' ' ' <<<"$executed"); do
  case "${x##*/}" in
    bash | sh | zsh | dash | ksh | fish | eval | exec | source | sudo | doas | su | xargs | nohup | timeout | nice | time | watch | parallel)
      executed="$(view R)"
      break
      ;;
  esac
done
while IFS= read -r piece; do
  read -ra words <<<"$piece"
  [ "${#words[@]}" = 0 ] && continue
  words=("${words[@]//[\"\'\\]/}")
  case "$(segment_decision "${words[@]}")" in
    deny | ask | unread) decisions+="unread " ;;
    allow | clean) ;;
    *) mentions "$piece" && decisions+="unread " ;;
  esac
done <<<"$executed"

reply() {
  jq -n --arg d "$1" --arg r "$2" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:$d,permissionDecisionReason:$r}}'
}

case "$decisions" in
  *deny*) reply deny "Push para main é negado: main só recebe merge de PR, feito pelo Rodrigo (AD-050). Faça push da branch <tipo>/<issue>/<slug> e abra o PR." ;;
  *ask*) reply ask "Merge, tag, release e mudança de proteção ou environment são passos do Rodrigo (AD-050): confirme antes de seguir." ;;
  *unread*) reply ask "O gate não lê com certeza um trecho que o bash executa e que cita git/gh com push, tag, merge, release ou api (substituição, ou texto passado a um shell): confirme que ele não faz push para main, merge, tag nem release (AD-050)." ;;
  *allow*) [ "$simple" = 1 ] && reply allow "Push de branch de feature e abertura de PR o agente faz sozinho (AD-050)." ;;
esac
exit 0
