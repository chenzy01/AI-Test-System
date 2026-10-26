"use client";
// NOTE  MC80OmFIVnBZMlhsdktEbXRLcmxqWm82YWs1VlVRPT06ZmRjMWI5OTI=

import React, { useState, useEffect, useCallback, Suspense } from "react";
import { useQueryState } from "nuqs";
import { getConfig, saveConfig, StandaloneConfig } from "@/lib/config";
import { ConfigDialog } from "@/app/components/ConfigDialog";
import { Button } from "@/components/ui/button";
import { Assistant } from "@langchain/langgraph-sdk";
import { ClientProvider, useClient } from "@/providers/ClientProvider";
import { Settings } from "lucide-react";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { ThreadList } from "@/app/components/ThreadList";
import { ChatProvider } from "@/providers/ChatProvider";
import { ChatInterface } from "@/app/components/ChatInterface";
// NOTE  MS80OmFIVnBZMlhsdktEbXRLcmxqWm82YWs1VlVRPT06ZmRjMWI5OTI=

interface HomePageInnerProps {
  config: StandaloneConfig;
  configDialogOpen: boolean;
  setConfigDialogOpen: (open: boolean) => void;
  handleSaveConfig: (config: StandaloneConfig) => void;
}

function HomePageInner({
  config,
  configDialogOpen,
  setConfigDialogOpen,
  handleSaveConfig,
}: HomePageInnerProps) {
  const client = useClient();
  const [threadId, setThreadId] = useQueryState("threadId");
  const [sidebar, setSidebar] = useQueryState("sidebar");

  const [mutateThreads, setMutateThreads] = useState<(() => void) | null>(null);
  const [interruptCount, setInterruptCount] = useState(0);
  const [assistant, setAssistant] = useState<Assistant | null>(null);

  const fetchAssistant = useCallback(async () => {
    const isUUID =
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
        config.assistantId
      );

    if (isUUID) {
      // We should try to fetch the assistant directly with this UUID
      try {
        const data = await client.assistants.get(config.assistantId);
        setAssistant(data);
      } catch (error) {
        console.error("Failed to fetch assistant:", error);
        setAssistant({
          assistant_id: config.assistantId,
          graph_id: config.assistantId,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          config: {},
          metadata: {},
          version: 1,
          name: "Assistant",
          context: {},
        });
      }
    } else {
      try {
        // We should try to list out the assistants for this graph, and then use the default one.
        // TODO: Paginate this search, but 100 should be enough for graph name
        const assistants = await client.assistants.search({
          graphId: config.assistantId,
          limit: 100,
        });
        const defaultAssistant = assistants.find(
          (assistant) => assistant.metadata?.["created_by"] === "system"
        );
        if (defaultAssistant === undefined) {
          throw new Error("No default assistant found");
        }
        setAssistant(defaultAssistant);
      } catch (error) {
        console.error(
          "Failed to find default assistant from graph_id: try setting the assistant_id directly:",
          error
        );
        setAssistant({
          assistant_id: config.assistantId,
          graph_id: config.assistantId,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          config: {},
          metadata: {},
          version: 1,
          name: config.assistantId,
          context: {},
        });
      }
    }
  }, [client, config.assistantId]);

  useEffect(() => {
    fetchAssistant();
  }, [fetchAssistant]);

  return (
    <>
      <ConfigDialog
        open={configDialogOpen}
        onOpenChange={setConfigDialogOpen}
        onSave={handleSaveConfig}
        initialConfig={config}
        currentAssistantId={config.assistantId}
      />
      <div className="flex h-screen flex-col bg-[#0F172A]">
        <header className="flex h-14 items-center justify-between border-b border-slate-700/50 bg-[#0F172A]/90 px-5 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-cyan-400 text-xs font-bold text-white shadow-lg shadow-blue-500/25">
                kk
              </div>
              <h1 className="text-base font-bold text-slate-100">
                CZY_AI测试平台
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setConfigDialogOpen(true)}
              className="rounded-lg text-sm text-slate-400 transition-colors hover:bg-slate-800 hover:text-slate-200"
            >
              <Settings className="mr-1.5 h-4 w-4" />
              设置
            </Button>
          </div>
        </header>

        <div className="flex-1 overflow-hidden">
          <ResizablePanelGroup
            direction="horizontal"
            autoSaveId="standalone-chat"
          >
            <ResizablePanel
              id="thread-history"
              order={1}
              defaultSize={sidebar ? 22 : 0}
              minSize={sidebar ? 18 : 0}
              maxSize={sidebar ? 40 : 0}
              className="relative min-w-[280px] border-r border-slate-700/50 bg-slate-900/50"
            >
              <ThreadList
                onThreadSelect={async (id) => {
                  await setThreadId(id);
                }}
                onNewThread={async () => {
                  await setThreadId(null);
                }}
                onMutateReady={(fn) => setMutateThreads(() => fn)}
                onClose={() => setSidebar(null)}
                onInterruptCountChange={setInterruptCount}
                isSidebarOpen={!!sidebar}
                onToggleSidebar={() => setSidebar(sidebar ? null : "1")}
              />
            </ResizablePanel>
            <ResizableHandle className="w-px bg-slate-700/50 transition-colors hover:bg-blue-500/50" />

            <ResizablePanel
              id="chat"
              className="relative flex flex-col"
              order={2}
            >
              <ChatProvider
                activeAssistant={assistant}
                onHistoryRevalidate={() => mutateThreads?.()}
              >
                <ChatInterface assistant={assistant} />
              </ChatProvider>
            </ResizablePanel>
          </ResizablePanelGroup>
        </div>
      </div>
    </>
  );
}
// eslint-disable  Mi80OmFIVnBZMlhsdktEbXRLcmxqWm82YWs1VlVRPT06ZmRjMWI5OTI=

function HomePageContent() {
  const [config, setConfig] = useState<StandaloneConfig | null>(null);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [assistantId, setAssistantId] = useQueryState("assistantId");

  // On mount, check for saved config, otherwise show config dialog
  useEffect(() => {
    const savedConfig = getConfig();
    if (savedConfig) {
      setConfig(savedConfig);
      if (!assistantId) {
        setAssistantId(savedConfig.assistantId);
      }
    } else {
      setConfigDialogOpen(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // If config changes, update the assistantId
  useEffect(() => {
    if (config && !assistantId) {
      setAssistantId(config.assistantId);
    }
  }, [config, assistantId, setAssistantId]);

  const handleSaveConfig = useCallback((newConfig: StandaloneConfig) => {
    saveConfig(newConfig);
    setConfig(newConfig);
  }, []);

  const langsmithApiKey =
    config?.langsmithApiKey || process.env.NEXT_PUBLIC_LANGSMITH_API_KEY || "";

  if (!config) {
    return (
      <>
        <ConfigDialog
          open={configDialogOpen}
          onOpenChange={setConfigDialogOpen}
          onSave={handleSaveConfig}
        />
        <div className="flex h-screen items-center justify-center bg-[#0F172A]">
          <div className="relative text-center">
            {/* Card */}
            <div className="relative rounded-2xl border border-slate-700/50 bg-slate-900/80 p-12 shadow-2xl shadow-black/30 backdrop-blur-sm">
              <div className="mb-6 text-5xl">🚀</div>
              <h1 className="text-3xl font-bold text-slate-100">
                欢迎使用CZY_AI测试平台
              </h1>
              <p className="mt-4 text-slate-400">
                智能、高效、可靠的 AI 驱动测试解决方案
              </p>
              <div className="mt-8 flex items-center justify-center gap-3">
                <Button
                  onClick={() => setConfigDialogOpen(true)}
                  size="lg"
                  className="rounded-lg bg-gradient-to-r from-blue-600 to-cyan-500 px-8 text-white shadow-lg shadow-blue-500/25 transition-all duration-200 hover:from-blue-700 hover:to-cyan-600 hover:shadow-xl hover:shadow-blue-500/40"
                >
                  <Settings className="mr-2 h-5 w-5" />
                  配置部署
                </Button>
              </div>
              <p className="mt-6 text-xs text-slate-500">
                首次使用请先配置部署地址和 API 密钥
              </p>
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <ClientProvider
      deploymentUrl={config.deploymentUrl}
      apiKey={langsmithApiKey}
    >
      <HomePageInner
        config={config}
        configDialogOpen={configDialogOpen}
        setConfigDialogOpen={setConfigDialogOpen}
        handleSaveConfig={handleSaveConfig}
      />
    </ClientProvider>
  );
}

export default function HomePage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center bg-[#0F172A]">
          <div className="text-center">
            <div className="mb-4 animate-pulse text-4xl">🚀</div>
            <p className="text-slate-400">加载中...</p>
          </div>
        </div>
      }
    >
      <HomePageContent />
    </Suspense>
  );
}
// NOTE  My80OmFIVnBZMlhsdktEbXRLcmxqWm82YWs1VlVRPT06ZmRjMWI5OTI=
