# README

While developing my new benchmark, dubbed Speed Test G PC, I noticed that the results were much slower on Windows compared to Linux.

I made a video about it here: https://youtu.be/8e7IdHG5fhQ

The problem seems to be the Visual Studio C/C++ compiler. Specifically, I am using "Microsoft (R) C/C++ Optimizing Compiler Version 19.24.28314 for x64"

Here is some source code which on my machine highlights the problem.

It would be great if other people could try this code on Windows, Linux, macOS, whatever using different compilers (but on the same hardware) so that I can find a fix
or workaround because at the moment it is invalidating my new benchmark as the compilers are introducing an unreasonable margin of error.

Thanks, Gary.
---
PS. No, I am not interested in your comments about coding style or how you would have formatted or arranged the code. This is JUST here to highlight the problem. Even optimizations which produce better results across ALL compilers are of little interest to me, to be honest, what I am interested in is finding out if others are seeing the same performance difference between Windows/Visual Studio and other compilers.
