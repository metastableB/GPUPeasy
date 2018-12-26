## GPUPeasy

GPU based parameters sweeps made easy.

This is a simple script that I made that can help me schedule a bunch of
parameter sweeps on one of more GPUs automatically. This is particularly useful
when jobs have varying running time and manually scheduling them is a pain.

I don't currently support scheduling over multiple machines.

Runs on `python3`. Based on `Flask` mainly.

I don't care what the job you want to schedule are as long as they are valid
shell commands. I just pass them onto `subprocess` to execute after specifying
which GPU to use.

## Features to Add
- [ ] Redo the schedule-job process such that it is amenable to network
  scheduling in the future.
- [ ] Support for changing devices. Adding/Subtracting GPU without killing the
  server. Ask the user to delete GPU objects and add new objects. So that I
  don't have to worry about killing/migrating processes.
- [ ] Support for checkpointing.
- [ ] Support for prioritizing jobs. This can be done by implementing priority
  queues. Replace the current list queue with priority queue that reduces to a
  regular queue with when priority = 30 or something.
- [ ] Implement a screen where you can view jobinfo and logs.
- [ ] Need to fix names and conventions throughout. 
