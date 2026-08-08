import React from "react";
import { Code2 } from "lucide-react";

const About: React.FC = () => {
  // Calculate years since starting coding.
  // Setting startYear to 2023 so it shows '2+' in 2025 and '3+' in 2026.
  const startYear = 2023;
  const currentYear = new Date().getFullYear();
  const yearsOfExperience = currentYear - startYear;

  return (
    <section id="about" className="py-24 px-6 relative">
      <div className="max-w-7xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Image Side */}
          <div className="relative">
            <div className="aspect-square rounded-3xl overflow-hidden border border-white/10 bg-white/5 relative group">
              <img
                src="/image/kamrul.jpeg"
                alt="Profile Work"
                className="w-full h-full object-cover grayscale opacity-80 group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-700"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-[#0a0a0a] via-transparent to-transparent opacity-60"></div>

              {/* Badge Overlay */}
              <div className="absolute bottom-6 left-6 right-6 bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-500/20 rounded-xl flex items-center justify-center text-blue-400">
                  <Code2 className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="font-bold text-white">Clean Code Advocate</h4>
                  <p className="text-sm text-gray-400">
                    Committed to Best Practices
                  </p>
                </div>
              </div>
            </div>

            {/* Decorative element */}
            <div className="absolute -top-6 -left-6 w-32 h-32 border-t-2 border-l-2 border-blue-500/30 rounded-tl-3xl -z-10"></div>
            <div className="absolute -bottom-6 -right-6 w-32 h-32 border-b-2 border-r-2 border-blue-500/30 rounded-br-3xl -z-10"></div>
          </div>

          {/* Text Side */}
          <div>
            <h2 className="text-4xl md:text-5xl font-bold mb-8">
              My Journey into{" "}
              <span className="text-blue-400">Software Engineering</span>
            </h2>
            <div className="space-y-6 text-gray-400 text-lg leading-relaxed">
              <p>
                Hello! I'm Kamrul Hasan Sojib, a passionate Computer Science
                undergraduate. My fascination with logic and problem-solving led
                me to the world of software development, where I strive to
                create impactful solutions.
              </p>
              <p>
                Currently, I specialize in the MERN stack (MongoDB, Express,
                React, Node), focusing on building seamless web applications. I
                believe that writing clean, efficient, and scalable code is not
                just a preference but a necessity in the modern tech landscape.
              </p>
              <p>
                Beyond web development, I am heavily invested in competitive
                programming and mastering complex algorithms using C and C++.
                I'm constantly learning new backend technologies to build more
                robust systems.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-6 mt-12">
              <div className="p-6 rounded-2xl bg-white/5 border border-white/10 group hover:border-blue-500/50 transition-all">
                <span className="block text-3xl font-bold text-white mb-1 group-hover:text-blue-400 transition-colors">
                  {yearsOfExperience}+
                </span>
                <span className="text-sm text-gray-500 uppercase tracking-wider">
                  Years Coding
                </span>
              </div>
              <div className="p-6 rounded-2xl bg-white/5 border border-white/10 group hover:border-blue-500/50 transition-all">
                <span className="block text-3xl font-bold text-white mb-1 group-hover:text-blue-400 transition-colors">
                  15+
                </span>
                <span className="text-sm text-gray-500 uppercase tracking-wider">
                  Projects Done
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default About;
