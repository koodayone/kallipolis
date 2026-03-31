import type { Metadata } from "next";
import { Inter, Days_One } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const daysOne = Days_One({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-days-one",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Kallipolis Atlas",
  description: "Institutional intelligence for California Community Colleges",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${daysOne.variable}`}>
      <body style={{ background: "#060d1f" }}>{children}</body>
    </html>
  );
}
