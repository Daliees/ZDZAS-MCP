module.exports = {
  apps: [
    {
      name: "ZDZAS-mcp",
      script: "/home/meetmaxim/Code/DS/ZDZAS-MCP/run_mcp.sh",
      env: {
        ZENDESK_SUBDOMAIN: process.env.ZENDESK_SUBDOMAIN,
        ZENDESK_EMAIL: process.env.ZENDESK_EMAIL,
        ZENDESK_API_KEY: process.env.ZENDESK_API_KEY,
        OPENAI_API_KEY: process.env.OPENAI_API_KEY,
      },
    },
    {
      name: "ZDZAS-chat",
      script: "/home/meetmaxim/Code/DS/ZDZAS-MCP/run_chat.sh",
      env: {
        ZENDESK_SUBDOMAIN: process.env.ZENDESK_SUBDOMAIN,
        ZENDESK_EMAIL: process.env.ZENDESK_EMAIL,
        ZENDESK_API_KEY: process.env.ZENDESK_API_KEY,
        OPENAI_API_KEY: process.env.OPENAI_API_KEY,
      },
    },
  ],
};

