// Plugin do opencode instalado por `grokbot-kit install opencode`.
// Fora de uma task (sem GROKBOT_KIT_TASK_ID no ambiente) não faz nada e não chama o grokbot-kit.
// O repasse de `permission.asked` e `question.asked` para `grokbot-kit emit --from opencode` chega no S3.
export const GrokbotKit = async () => {
  if (!process.env.GROKBOT_KIT_TASK_ID) return {}
  return {}
}
