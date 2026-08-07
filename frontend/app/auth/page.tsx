"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { useReducedMotion } from "@/hooks/use-reduced-motion";
import { useAuth } from "@/context/auth-provider";

type Mode = "login" | "register";
type Status = "idle" | "loading" | "success" | "error";

const formVariants = {
  enter: (direction: number) => ({ x: direction > 0 ? 24 : -24, opacity: 0 }),
  center: { x: 0, opacity: 1 },
  exit: (direction: number) => ({ x: direction > 0 ? -24 : 24, opacity: 0 }),
};

export default function AuthPage() {
  const [mode, setMode] = React.useState<Mode>("login");
  const [status, setStatus] = React.useState<Status>("idle");
  const [direction, setDirection] = React.useState(0);
  const [errorMsg, setErrorMsg] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [name, setName] = React.useState("");
  const reduced = useReducedMotion();
  const isLogin = mode === "login";
  const router = useRouter();
  const { signIn, signUp, user } = useAuth();

  // Redirect if already logged in
  React.useEffect(() => {
    if (user) router.replace("/dashboard");
  }, [user, router]);

  function switchMode(next: Mode) {
    setDirection(next === "register" ? 1 : -1);
    setMode(next);
    setErrorMsg("");
    setStatus("idle");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (status === "loading") return;
    setStatus("loading");
    setErrorMsg("");

    let result;
    if (isLogin) {
      result = await signIn(email, password);
    } else {
      result = await signUp(email, password, name || undefined);
    }

    if (result.error) {
      setErrorMsg(result.error);
      setStatus("error");
    } else if (!isLogin && !('session' in result ? result.session : true)) {
      // If we signed up but got no session, email confirmation is required
      setStatus("success");
      setErrorMsg("Registration successful! Please check your email to verify your account.");
    } else {
      setStatus("success");
      // Small delay for the success animation, then redirect
      setTimeout(() => router.push("/dashboard"), 600);
    }
  }

  return (
    <div className="grid min-h-screen bg-cream dark:bg-[#161611] md:grid-cols-[1.1fr_1fr]">
      <div className="relative flex flex-col justify-between overflow-hidden bg-ink p-10 text-cream md:p-12">
        <Link href="/" className="font-heading text-xl font-semibold transition-opacity hover:opacity-80">
          Wardrobe.AI
        </Link>
        <div className="flex flex-1 items-center justify-center">
          <svg width="220" height="260" viewBox="0 0 200 240" fill="none">
            <motion.path
              d="M100,18 L74,18 L42,52 L16,108 L38,120 L38,222 L162,222 L162,120 L184,108 L158,52 L126,18 Z"
              pathLength={1}
              stroke={status === "success" ? "#C9A45C" : "#F8F7F4"}
              strokeWidth={3}
              fill={status === "success" ? "#C9A45C" : "none"}
              initial={{ pathLength: 0 }}
              animate={{ pathLength: status === "success" ? 1 : reduced ? 1 : [0, 1, 0] }}
              transition={
                status === "success"
                  ? { duration: 0.5 }
                  : reduced
                    ? { duration: 0 }
                    : { duration: 5, repeat: Infinity, ease: "easeInOut" }
              }
            />
          </svg>
        </div>
        <p className="max-w-[32ch] font-sans text-[13px] leading-relaxed text-cream/60">
          One wardrobe. Understood, worn, and ready.
        </p>
      </div>

      <div className="flex items-center justify-center p-10 md:p-12">
        <div className="w-full max-w-[380px]">
          <AnimatePresence mode="wait">
            {status !== "success" ? (
              <motion.div key="form-shell" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <div className="relative mb-8 flex w-full rounded-full bg-card p-1 shadow-[0_4px_16px_rgba(30,30,30,0.06)]">
                  <motion.div
                    className="absolute inset-y-1 rounded-full bg-forest dark:bg-[#3d6b54]"
                    layout
                    transition={{ type: "spring", stiffness: 400, damping: 30 }}
                    style={{
                      left: isLogin ? 4 : "50%",
                      right: isLogin ? "50%" : 4,
                    }}
                  />
                  <button
                    onClick={() => switchMode("login")}
                    className={cn(
                      "relative z-10 flex-1 rounded-full py-2.5 font-sans text-[13.5px] font-semibold transition-colors",
                      isLogin ? "text-cream" : "text-ink dark:text-cream"
                    )}
                  >
                    Log in
                  </button>
                  <button
                    onClick={() => switchMode("register")}
                    className={cn(
                      "relative z-10 flex-1 rounded-full py-2.5 font-sans text-[13.5px] font-semibold transition-colors",
                      !isLogin ? "text-cream" : "text-ink dark:text-cream"
                    )}
                  >
                    Register
                  </button>
                </div>

                <AnimatePresence mode="wait" custom={direction}>
                  <motion.div
                    key={mode}
                    custom={direction}
                    variants={formVariants}
                    initial="enter"
                    animate="center"
                    exit="exit"
                    transition={{ type: "spring", stiffness: 320, damping: 30 }}
                  >
                    <h1 className="mb-1.5 font-heading text-[28px] font-semibold text-ink dark:text-cream">
                      {isLogin ? "Welcome back" : "Create your account"}
                    </h1>
                    <p className="mb-7 font-sans text-[14.5px] text-ink/55 dark:text-cream/55">
                      {isLogin ? "Log in to your wardrobe." : "A minute to set up. Free to start."}
                    </p>

                    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                      <AnimatePresence>
                        {!isLogin && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                          >
                            <label className="mb-1.5 block font-mono text-[11px] tracking-wide text-ink/50 dark:text-cream/50">
                              NAME
                            </label>
                            <Input
                              placeholder="Your name"
                              value={name}
                              onChange={(e) => setName(e.target.value)}
                            />
                          </motion.div>
                        )}
                      </AnimatePresence>
                      <div>
                        <label className="mb-1.5 block font-mono text-[11px] tracking-wide text-ink/50 dark:text-cream/50">
                          EMAIL
                        </label>
                        <Input
                          type="email"
                          placeholder="you@example.com"
                          required
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                        />
                      </div>
                      <div>
                        <label className="mb-1.5 block font-mono text-[11px] tracking-wide text-ink/50 dark:text-cream/50">
                          PASSWORD
                        </label>
                        <Input
                          type="password"
                          placeholder="••••••••"
                          required
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                        />
                      </div>

                      {errorMsg && (
                        <motion.p
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          className="font-sans text-[13px] font-semibold text-[#B5502F]"
                        >
                          {errorMsg}
                        </motion.p>
                      )}

                      <Button type="submit" size="lg" className="mt-1 w-full justify-center" disabled={status === "loading"}>
                        {status === "loading" ? "One moment…" : isLogin ? "Log in" : "Register"}
                      </Button>
                    </form>
                  </motion.div>
                </AnimatePresence>
              </motion.div>
            ) : (
              <motion.div key="success" initial={{ opacity: 0, scale: 0.92 }} animate={{ opacity: 1, scale: 1 }}>
                <p className="mb-3 font-mono text-[11px] tracking-wide text-gold">{isLogin ? "LOGGED IN" : "REGISTERED"}</p>
                <h1 className="mb-3 font-heading text-[32px] font-semibold text-ink dark:text-cream">You&apos;re in.</h1>
                <p className="mb-7 max-w-[38ch] font-sans text-[15px] leading-relaxed text-ink/60 dark:text-cream/60">
                  Your wardrobe is ready. Start with your first upload.
                </p>
                <Link href="/dashboard">
                  <Button size="lg">Continue</Button>
                </Link>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
