import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(req: NextRequest) {
  const host = req.headers.get("host") || "";
  const url = req.nextUrl.clone();
  const { pathname } = url;

  // Determine if this request is on the editorial admin subdomain
  const configuredAdminHost = process.env.NEXT_PUBLIC_ADMIN_HOST;
  const isAdminSubdomain =
    host.toLowerCase().startsWith("admin.") ||
    (configuredAdminHost ? host.toLowerCase() === configuredAdminHost.toLowerCase() : false) ||
    url.searchParams.get("subdomain") === "admin";

  const isLocalOrDev =
    host.toLowerCase().includes("localhost") ||
    host.toLowerCase().includes("127.0.0.1") ||
    process.env.NODE_ENV !== "production";

  if (isAdminSubdomain) {
    // On the admin subdomain:
    // Route root / to /admin
    if (pathname === "/") {
      url.pathname = "/admin";
      return NextResponse.rewrite(url);
    }
    // Route clean subpaths: /sources -> /admin/sources, etc.
    const adminSubpaths = ["clusters", "sources", "review", "entities", "cost", "quarantine", "dead-letters"];
    const firstSegment = pathname.split("/")[1];
    if (adminSubpaths.includes(firstSegment)) {
      url.pathname = `/admin${pathname}`;
      return NextResponse.rewrite(url);
    }
    // Allow direct /admin paths
    if (pathname.startsWith("/admin")) {
      return NextResponse.next();
    }
    // For other paths on the admin subdomain, pass through or allow
    return NextResponse.next();
  }

  // In local development or testing, permit direct access to /admin and /admin/*
  if (isLocalOrDev) {
    return NextResponse.next();
  }

  // On the public client / reader domain in production:
  // Strictly forbid access to /admin or /admin/* -> return 404 Not Found
  if (pathname === "/admin" || pathname.startsWith("/admin/")) {
    url.pathname = "/_not-found";
    return NextResponse.rewrite(url, { status: 404 });
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
