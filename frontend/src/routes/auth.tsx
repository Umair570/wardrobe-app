import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { motion } from "motion/react";
import { useState } from "react";
import { ArrowLeft, Lock, Mail } from "lucide-react";
import heroModel from "@/assets/hero-model.jpg";
import { Button } from "@/components/ui/LuxButton";
import { Eyebrow } from "@/components/ui/Surface";
import { supabase } from "@/lib/supabase";
import { toast } from "sonner";

export const Route = createFileRoute("/auth")({
  head: () => ({
    meta: [
      { title: "Sign in — Atelier AI Wardrobe" },
      { name: "description", content: "Sign in or create your Atelier account to access your digital wardrobe and AI stylist." },
      { property: "og:title", content: "Sign in — Atelier AI Wardrobe" },
      { property: "og:description", content: "Access your digital wardrobe and AI stylist." },
    ],
  }),
  component: AuthPage,
});

function AuthPage() {
  const [mode, setMode] = useState<"signin" | "register">("signin");
  const [pending, setPending] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const navigate = useNavigate();

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setPending(true);

    try {
      if (mode === "register") {
        if (password !== confirmPassword) {
          toast.error("Passwords do not match");
          setPending(false);
          return;
        }
        const { error } = await supabase.auth.signUp({
          email,
          password,
        });
        if (error) throw error;
        toast.success("Registration successful! You can now log in.");
        setMode("signin");
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (error) throw error;
        toast.success("Successfully logged in");
        navigate({ to: "/dashboard" });
      }
    } catch (err: any) {
      toast.error(err.message || "Authentication failed");
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden lg:block">
        <img
          src={heroModel}
          alt="Editorial fashion portrait"
          width={1024}
          height={1280}
          className="h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-ink/35" />
        <div className="absolute bottom-12 left-12 max-w-xs">
          <h2 className="text-4xl uppercase text-beige display-xl">Dress from your own closet</h2>
        </div>
      </div>

      <div className="flex items-center justify-center px-6 py-14">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="w-full max-w-sm"
        >
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-[0.62rem] font-bold uppercase tracking-[0.28em] text-muted-foreground transition-colors hover:text-forest"
          >
            <ArrowLeft className="h-3 w-3" /> Back
          </Link>

          <Eyebrow className="mt-10">Atelier account</Eyebrow>
          <h1 className="mt-4 text-4xl uppercase display-xl">
            {mode === "signin" ? "Welcome back" : "Join atelier"}
          </h1>

          <div className="mt-8 flex rounded-full bg-secondary p-1">
            {(["signin", "register"] as const).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                type="button"
                className={`flex-1 rounded-full py-2.5 text-[0.62rem] font-bold uppercase tracking-[0.2em] transition-all duration-300 ${
                  mode === m ? "bg-ink text-beige" : "text-muted-foreground"
                }`}
              >
                {m === "signin" ? "Sign in" : "Register"}
              </button>
            ))}
          </div>

          <form
            className="mt-7 space-y-3"
            onSubmit={handleAuth}
          >
            <Field 
              icon={Mail} 
              type="email" 
              placeholder="Email address" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <Field 
              icon={Lock} 
              type="password" 
              placeholder="Password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            {mode === "register" && (
              <Field 
                icon={Lock} 
                type="password" 
                placeholder="Confirm password" 
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            )}
            <Button type="submit" size="lg" className="w-full" disabled={pending}>
              {pending ? "One moment…" : mode === "signin" ? "Sign in" : "Create account"}
            </Button>
          </form>

          <p className="mt-6 text-center text-xs text-muted-foreground">
            Secured with Supabase Auth.
          </p>
        </motion.div>
      </div>
    </div>
  );
}

function Field({
  icon: Icon,
  ...rest
}: { icon: typeof Mail } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-border bg-card px-4 transition-colors focus-within:border-forest">
      <Icon className="h-4 w-4 text-muted-foreground" />
      <input
        required
        className="h-13 w-full bg-transparent py-4 text-sm outline-none placeholder:text-muted-foreground"
        {...rest}
      />
    </div>
  );
}