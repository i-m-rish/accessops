import Link from "next/link";

export default function Home() {
  return (
    <main style={{ display: "flex", gap: 12 }}>
      <Link href="/login">Login</Link>
      <Link href="/register">Register</Link>
      <Link href="/request">My Requests</Link>
      <Link href="/approvals">Approvals</Link>
    </main>
  );
}
